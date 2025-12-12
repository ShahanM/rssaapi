import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient
from rssa_api.auth.authorization import authorize_api_key_for_study
from rssa_api.apps.study.main import api as study_api
from rssa_api.main import app
from rssa_api.data.models.study_components import Study, StudyStep, User
from rssa_api.data.rssadb import get_db


@pytest.mark.asyncio
async def test_get_first_step(client: AsyncClient, db_session, seed_study, seed_user):
    # Seed step
    step_id = uuid.uuid4()
    step = StudyStep(
        id=step_id, 
        study_id=seed_study.id, 
        name="Consent",
        description="Consent Step",
        path="/consent", 
        step_type="consent", 
        order_position=1,
        created_by_id=seed_user.id
    )
    db_session.add(step)
    await db_session.commit()
    
    # Override auth
    async def override_auth():
        return seed_study.id
        
    study_api.dependency_overrides[authorize_api_key_for_study] = override_auth

    # Override get_db for study_api
    async def override_get_db():
        yield db_session
    
    study_api.dependency_overrides[get_db] = override_get_db
    # Clear root_path for testing to avoid routing issues with AsyncClient
    app.root_path = ""
    
    response = await client.get(f"/study/studies/{seed_study.id}/steps/first")
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == str(step_id)
    assert data["data"]["path"] == "/consent"
