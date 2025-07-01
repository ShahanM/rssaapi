import logging
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.survey_construct_schemas import SurveyConstructSchema
from data.services.survey_construct_service import SurveyConstructService
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.resources.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/v2/admin',
	tags=[Tags.construct],
	dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get('/constructs/', response_model=List[SurveyConstructSchema])
async def get_studies(
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	construct_service = SurveyConstructService(db)
	constructs_in_db = await construct_service.get_survey_constructs()

	converted = [SurveyConstructSchema.model_validate(c) for c in constructs_in_db]

	return converted
