import pytest
from httpx import AsyncClient
from rssa_api.main import app
from rssa_api.auth.security import get_auth0_authenticated_user
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.services.recommendation.registry import REGISTRY

@pytest.mark.asyncio
async def test_get_recommender_keys(client: AsyncClient):
    # Mock Auth0 user with required permissions
    async def override_get_auth0_authenticated_user():
        return Auth0UserSchema(
            sub="auth0|testadmin",
            email="admin@test.com",
            permissions=["admin:all"]
        )
    
    from rssa_api.apps.admin.main import api as admin_api
    
    app.dependency_overrides[get_auth0_authenticated_user] = override_get_auth0_authenticated_user
    admin_api.dependency_overrides[get_auth0_authenticated_user] = override_get_auth0_authenticated_user
    
    # Clear root_path for testing to avoid routing issues with AsyncClient
    original_root_path = app.root_path
    app.root_path = ""
    
    try:
        response = await client.get("/admin/conditions/recommender-keys")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify keys match the registry
        registry_keys = set(REGISTRY.keys())
        response_keys = {item['id'] for item in data}
        
        assert registry_keys == response_keys
        
        # Check structure
        first_item = data[0]
        assert "id" in first_item
        assert "name" in first_item
        
    finally:
        app.dependency_overrides = {}
        admin_api.dependency_overrides = {}
