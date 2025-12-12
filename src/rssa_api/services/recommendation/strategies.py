import json
import logging
from typing import Any, Optional, Protocol

from aiobotocore.session import get_session
from botocore.exceptions import ClientError

from rssa_api.data.schemas.recommendations import (
    EnrichedRecResponse,
    RecommendationResponse,
    StandardRecResponse,
)

log = logging.getLogger(__name__)


class RecommendationStrategy(Protocol):
    async def recommend(
        self, user_id: str, ratings: list[Any], limit: int, run_config: Optional[dict] = None
    ) -> RecommendationResponse: ...


class LambdaStrategy:
    """Invokes an AWS Lambda function for recommendations."""

    def __init__(self, function_name: str, payload_template: dict, region_name: str = 'us-east-1'):
        self.logical_function_name = function_name
        self.resolved_function_name: Optional[str] = None
        self.payload_template = payload_template
        self.region_name = region_name
        self._session = get_session()

    async def _resolve_function_name(self, client) -> str:
        """Finds the full Lambda function name given a partial (logical) name.

        AWS SAM appends a unique suffix to the function name (e.g., 'ImplicitMFErsRecsFunction-AbCdEf12').
        We match if the function name *starts with* the logical name.
        """
        if self.resolved_function_name:
            return self.resolved_function_name

        try:
            # List functions and look for a match
            # This is a bit expensive, so we cache it.
            # In a production environment, we might prefer passing the full name via env vars.
            paginator = client.get_paginator('list_functions')
            async for page in paginator.paginate():
                for func in page['Functions']:
                    fname = func['FunctionName']
                    # SAM usually does "StackName-LogicalID-Suffix".
                    # We'll check if the logical name exists anywhere in the function name.
                    if self.logical_function_name in fname:
                        log.info(f"Resolved Lambda {self.logical_function_name} -> {fname}")
                        self.resolved_function_name = fname
                        return fname
            
            log.warning(f"Could not resolve full name for {self.logical_function_name}. Using as-is.")
            self.resolved_function_name = self.logical_function_name
            return self.logical_function_name

        except Exception as e:
            log.error(f"Error resolving lambda name: {e}")
            return self.logical_function_name

    async def recommend(
        self, user_id: str, ratings: list[Any], limit: int, run_config: Optional[dict] = None
    ) -> RecommendationResponse:
        """
        Invokes the Lambda function.
        """
        # Construct Payload
        payload = self.payload_template.copy()
        if run_config:
            payload.update(run_config)

        payload['user_id'] = str(user_id)
        payload['limit'] = limit  # Ensure limit is passed
        
        # Ratings: list of {item_id: str, rating: float}
        payload['ratings'] = [r.model_dump() for r in ratings]

        # Invoke Lambda
        try:
            async with self._session.create_client('lambda', region_name=self.region_name) as client:
                
                real_function_name = await self._resolve_function_name(client)

                response = await client.invoke(
                    FunctionName=real_function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload),
                )

                # Read Response
                payload_stream = await response['Payload'].read()
                response_data = json.loads(payload_stream)

                if 'FunctionError' in response:
                    error_msg = response_data.get('errorMessage', 'Unknown Lambda Error')
                    log.error(f"Lambda {real_function_name} failed: {error_msg}")
                    raise RuntimeError(f"Recommendation Engine Error: {error_msg}")

                # Parse Response
                # Handle direct list return or dict with items
                items = []
                log.info(f"Lambda Raw Response: {response_data}")

                if isinstance(response_data, list):
                    items = response_data
                elif isinstance(response_data, dict):
                    if 'items' in response_data:
                        items = response_data['items']
                    # Handle API Gateway style body wrapper if necessary
                    elif 'body' in response_data:
                        body = response_data['body']
                        if isinstance(body, str):
                            body = json.loads(body)
                        if isinstance(body, list):
                            items = body
                        elif isinstance(body, dict) and 'items' in body:
                            items = body['items']
                
                log.info(f"Parsed Items: {items}")
                
                return StandardRecResponse(items=items, total_count=len(items))

        except Exception as e:
            log.error(f"Error invoking Lambda strategy {self.logical_function_name}: {e}")
            raise e
