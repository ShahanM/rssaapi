"""Tests for Admin API routers."""

import pytest

from rssa_api.apps.admin.routers import api_keys, movies, users
from rssa_api.apps.admin.routers.study_components import studies
from rssa_api.apps.admin.routers.survey_constructs import survey_constructs, survey_items


@pytest.mark.asyncio
async def test_admin_routers_structure() -> None:
    """Verifies that admin routers are importable and have expected routes.

    This acts as a sanity check for the router configuration.
    """
    assert survey_constructs.router is not None
    assert survey_items.router is not None
    assert studies.router is not None
    assert users.router is not None
    assert api_keys.router is not None
    assert movies.router is not None

    # Check for PATCH endpoint in survey_constructs
    routes = [r.path for r in survey_constructs.router.routes]
    assert '/constructs/{construct_id}' in routes

    # Check for PATCH endpoint in survey_items
    item_routes = [r.path for r in survey_items.router.routes]
    assert '/items/{item_id}' in item_routes

    # Check users router path
    user_routes = [r.path for r in users.router.routes]
    assert '/users/' in user_routes
