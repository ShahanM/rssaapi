import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import get_auth0_authenticated_user, require_permissions
from data.schemas import Auth0UserSchema
from data.schemas.study_components import StudyConditionBaseSchema
from data.services import StudyConditionService
from data.services.rssa_dependencies import get_study_condition_service as conditions_service
from docs.admin_docs import Tags

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/conditions',
	tags=[Tags.condition],
	dependencies=[Depends(get_auth0_authenticated_user), Depends(conditions_service)],
)


@router.get('/{condition_id}', response_model=StudyConditionBaseSchema)
async def get_item(
	condition_id: uuid.UUID,
	service: Annotated[StudyConditionService, Depends(conditions_service)],
	user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'read:conditions'))],
):
	condition = await service.get_study_condition(condition_id)
	if condition is None:
		raise (HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study condition was not found.'))

	return condition
