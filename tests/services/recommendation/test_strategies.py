"""Tests for LambdaStrategy."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rssa_api.data.schemas.recommendations import ResponseWrapper
from rssa_api.services.recommendation.strategies import LambdaStrategy


@pytest.fixture
def mock_session():
    """Mocks the session for testing."""
    with patch('rssa_api.services.recommendation.strategies.get_session') as mock:
        yield mock


@pytest.mark.asyncio
async def test_resolve_function_name(mock_session):
    """Test resolving function name from logical name."""
    strategy = LambdaStrategy('ImplicitMF', {}, 'us-east-1')

    mock_client = AsyncMock()
    # Mock paginator for list_functions to be synchronous
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value.__aiter__.return_value = [
        {'Functions': [{'FunctionName': 'ImplicitMFErsRecsFunction-12345'}]}
    ]
    # Important: get_paginator is synchronous in boto3/aiobotocore
    mock_client.get_paginator = MagicMock(return_value=mock_paginator)

    result = await strategy._resolve_function_name(mock_client)

    assert result == 'ImplicitMFErsRecsFunction-12345'
    assert strategy.resolved_function_name == result

    # Test cache hit
    result2 = await strategy._resolve_function_name(mock_client)
    assert result2 == result
    assert mock_client.get_paginator.call_count == 1  # called once


@pytest.mark.asyncio
async def test_recommend_success(mock_session):
    """Test successful recommendation invocation."""
    strategy = LambdaStrategy('ImplicitMF', {}, 'us-east-1')
    strategy.resolved_function_name = 'ResolvedFunc'  # skip resolution

    # Mock Lambda Client
    mock_client = AsyncMock()
    mock_session.return_value.create_client.return_value.__aenter__.return_value = mock_client

    # Mock Response
    response_body = {'items': [101, 102], 'response_type': 'standard', 'total_count': 2}
    mock_payload_stream = AsyncMock()
    mock_payload_stream.read.return_value = json.dumps({'body': json.dumps(response_body)}).encode()

    mock_invoke_resp = {'Payload': mock_payload_stream}
    mock_client.invoke.return_value = mock_invoke_resp

    # Call
    from rssa_api.data.schemas.participant_response_schemas import MovieLensRating

    ratings = [MovieLensRating(item_id='1', rating=5.0)]

    result = await strategy.recommend(user_id='u1', ratings=ratings, limit=10)

    assert isinstance(result, ResponseWrapper)
    assert len(result.items) == 2
    mock_client.invoke.assert_called_once()


@pytest.mark.asyncio
async def test_recommend_lambda_error(mock_session):
    """Test handling of Lambda function error."""
    strategy = LambdaStrategy('ImplicitMF', {}, 'us-east-1')
    strategy.resolved_function_name = 'ResolvedFunc'

    mock_client = AsyncMock()
    mock_session.return_value.create_client.return_value.__aenter__.return_value = mock_client

    mock_payload_stream = AsyncMock()
    mock_payload_stream.read.return_value = json.dumps({'errorMessage': 'Something went wrong'}).encode()

    mock_invoke_resp = {'Payload': mock_payload_stream, 'FunctionError': 'Unhandled'}
    mock_client.invoke.return_value = mock_invoke_resp

    with pytest.raises(RuntimeError, match='Recommendation Engine Error: Something went wrong'):
        await strategy.recommend('u1', [], 10)
