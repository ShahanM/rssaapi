"""Strategies for recommendations."""

import json
from typing import Any, Protocol, cast

import httpx
import structlog
from aiobotocore.session import get_session
from asgi_correlation_id import correlation_id
from pydantic import TypeAdapter
from types_aiobotocore_lambda.client import LambdaClient

from rssa_api.data.schemas.participant_response_schemas import MovieLensRating
from rssa_api.data.schemas.recommendations import (
    ResponseWrapper,
)

logger = structlog.getLogger(__name__)


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
        payload['limit'] = limit
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
                    logger.error(f'Lambda {self.logical_function_name} failed: {error_msg}')
                    raise RuntimeError(f'Recommendation Engine Error: {error_msg}')

                logger.info(f'Lambda Raw Response: {response_data}')

                adapter = TypeAdapter(ResponseWrapper)
                return adapter.validate_json(response_data['body'])

        except Exception as e:
            logger.error(f'Error invoking Lambda strategy {self.logical_function_name}: {e}')
            raise e


"""
Local Development Overrides

The following endpoint is used by the Docker dev network.
"""


class LocalDevStrategy:
    """Invokes the local FastAPI recommender simulator via HTTP."""

    def __init__(self, local_url: str, payload_template: dict):
        self.local_url = local_url
        self.payload_template = payload_template

    async def recommend(
        self, user_id: str, ratings: list[MovieLensRating], limit: int, run_config: dict | None = None
    ) -> ResponseWrapper:

        logger.info('Requestion recommendations', user_id=user_id)
        current_req_id = correlation_id.get()
        headers = {'X-Request-ID': current_req_id, 'Content-Type': 'application/json'}

        payload = self.payload_template.copy()
        if run_config:
            payload.update(run_config)

        payload['user_id'] = str(user_id)
        payload['ratings'] = [r.model_dump() for r in ratings]
        payload['limit'] = limit

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.local_url, json=payload, headers=headers, timeout=30.0)
                response.raise_for_status()
                response_data = response.json()

                logger.info(f'Local Dev Simulator Raw Response: {response_data}')
                body = response_data.get('body', response_data)
                if isinstance(body, str):
                    body = json.loads(body)

                adapter = TypeAdapter(ResponseWrapper)
                return adapter.validate_json(json.dumps(body))

        except Exception as e:
            logger.error(f'Error invoking LocalDevStrategy at {self.local_url}: {e}')
            raise e
