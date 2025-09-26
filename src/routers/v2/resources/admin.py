from typing import Annotated

from fastapi import APIRouter, Depends, Query

from data.services import AdminService, MovieService
from data.services.content_dependencies import get_movie_service
from data.services.rssa_dependencies import get_admin_service

router = APIRouter(
	prefix='/admin',
	tags=['Admin'],
)

# FIXME: THIS SHOULD BE A PART OF THE DASHBOARD!!!


@router.post('/create_pre_shuffled', response_model=bool)
async def new_preshuffled_movie_list(
	movie_service: Annotated[MovieService, Depends(get_movie_service)],
	admin_service: Annotated[AdminService, Depends(get_admin_service)],
	seed: int = Query(),
):
	ers_movies = await movie_service.get_movies_with_emotions()
	movie_ids = [m.id for m in ers_movies]
	await admin_service.create_pre_shuffled_movie_list(movie_ids, 'ers', seed)

	return True
