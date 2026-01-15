"""Tests for the studies router."""

import uuid

import pytest
from httpx import AsyncClient
from rssa_storage.rssadb.models.study_components import StudyStep

from rssa_api.apps.study.main import api as study_api
from rssa_api.auth.authorization import authorize_api_key_for_study
from rssa_api.data.sources.rssadb import rssa_db
from rssa_api.main import app


@pytest.mark.asyncio
async def test_get_first_step(client: AsyncClient, db_session, seed_study, seed_user) -> None:
    """Verifies that the first step of a study can be retrieved.

    Ensures correct routing and database interaction for study steps.
    """
    # Seed step
    step_id = uuid.uuid4()
    step = StudyStep(
        id=step_id,
        study_id=seed_study.id,
        name='Consent',
        description='Consent Step',
        path='/consent',
        step_type='consent',
        order_position=1,
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

    study_api.dependency_overrides[rssa_db] = override_get_db
    # Clear root_path for testing to avoid routing issues with AsyncClient
    app.root_path = ''

    response = await client.get(f'/study/studies/{seed_study.id}/steps/first')

    assert response.status_code == 200
    data = response.json()
    assert data['data']['id'] == str(step_id)
    assert data['data']['path'] == '/consent'
