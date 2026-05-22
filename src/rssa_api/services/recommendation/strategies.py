"""Strategies for recommendations."""

import json
from typing import Any, Protocol, cast

import structlog
from aiobotocore.session import get_session
from pydantic import TypeAdapter
from types_aiobotocore_lambda.client import LambdaClient

from rssa_api.data.schemas.participant_response_schemas import MovieLensRating
from rssa_api.data.schemas.recommendations import (
    ResponseWrapper,
)

log = structlog.getLogger(__name__)


class RecommendationStrategy(Protocol):
    """Protocol for recommendation strategies."""

    async def recommend(
        self, user_id: str, ratings: list[Any], limit: int, run_config: dict | None = None
    ) -> ResponseWrapper: ...


class LambdaStrategy:
    """Invokes an AWS Lambda function for recommendations."""

    def __init__(self, function_name: str, payload_template: dict, region_name: str = 'us-east-1'):
        self.logical_function_name = function_name
        self.resolved_function_name: str | None = None
        self.payload_template = payload_template
        self.region_name = region_name
        self._session = get_session()

    async def recommend(
        self, user_id: str, ratings: list[MovieLensRating], limit: int, run_config: dict | None = None
    ) -> ResponseWrapper:
        """Invokes the Lambda function."""
        payload = self.payload_template.copy()
        if run_config:
            payload.update(run_config)
        payload['user_id'] = str(user_id)
        payload['ratings'] = [r.model_dump() for r in ratings]
        payload['limit'] = limit  # Ensure limit is passed
        try:
            async with self._session.create_client('lambda', region_name=self.region_name) as client:
                lambda_client = cast(LambdaClient, client)
                response = await lambda_client.invoke(
                    FunctionName=self.logical_function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload, default=str),
                )

                payload_stream = await response['Payload'].read()
                response_data = json.loads(payload_stream)

                if 'FunctionError' in response:
                    error_msg = response_data.get('errorMessage', 'Unknown Lambda Error')
                    log.error(f'Lambda {self.logical_function_name} failed: {error_msg}')
                    raise RuntimeError(f'Recommendation Engine Error: {error_msg}')

                log.info(f'Lambda Raw Response: {response_data}')

                adapter = TypeAdapter(ResponseWrapper)
                return adapter.validate_json(response_data['body'])
                # return ResponseWrapper.model_validate_json(response_data['body'])

        except Exception as e:
            log.error(f'Error invoking Lambda strategy {self.logical_function_name}: {e}')
            raise e
