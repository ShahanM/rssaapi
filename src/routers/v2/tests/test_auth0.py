import logging

import pytest

from src.router.v2.auth0 import (
	create_permission_scope,
	delete_permission_scope,
	get_management_api_token,
	get_resource_server_scopes,
)

logging.basicConfig(level=logging.INFO)

AUTH0_TEST_USER_ID = 'auth0|66819c40e00f74d06b00e7d7'
AUTH0_TEST_PERMISSION_NAME = 'test:resource:resource_id'
AUTH0_TEST_PERMISSION_DESCRIPTION = 'Test permission description'


@pytest.mark.asyncio
async def test_get_management_api_token():
	token = await get_management_api_token()
	assert token is not None
	assert isinstance(token, str)


@pytest.mark.asyncio
async def test_get_resource_server_scopes():
	token = await get_management_api_token()
	assert token is not None

	scopes = await get_resource_server_scopes(token)
	assert scopes is not None
	assert isinstance(scopes, list)


@pytest.mark.asyncio
async def test_create_and_delete_permission():
	token = await get_management_api_token()

	current_scopes = await get_resource_server_scopes(token)

	new_scopes = await create_permission_scope(AUTH0_TEST_PERMISSION_NAME, AUTH0_TEST_PERMISSION_DESCRIPTION)
	assert new_scopes is not None

	current_scopes_set = {scope['value'] for scope in current_scopes}
	new_scopes_set = {scope['value'] for scope in new_scopes}

	assert AUTH0_TEST_PERMISSION_NAME not in current_scopes_set
	assert AUTH0_TEST_PERMISSION_NAME in new_scopes_set

	new_scope = (new_scopes_set - current_scopes_set).pop()
	assert new_scope == AUTH0_TEST_PERMISSION_NAME
	new_scopes_set.discard(new_scope)
	assert new_scopes_set == current_scopes_set

	# Clean up by deleting the permission scope
	cleaned_scopes = await delete_permission_scope(AUTH0_TEST_PERMISSION_NAME)
	assert cleaned_scopes is not None

	cleaned_scopes_set = {scope['value'] for scope in cleaned_scopes}
	assert AUTH0_TEST_PERMISSION_NAME not in cleaned_scopes_set
	assert cleaned_scopes_set == current_scopes_set

