from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from data.moviedb import get_db as movie_db
from data.rssadb import get_db as rssa_db
from data.services.admin_service import AdminService
from data.services.movie_service import MovieService
from docs.metadata import TagsMetadataEnum as Tags

router = APIRouter(
	prefix='/v2',
	tags=[Tags.admin],
)


@router.post('/admin/create_pre_shuffled', response_model=bool)
async def new_preshuffled_movie_list(
	seed: int = Query(),
	rssadb: AsyncSession = Depends(rssa_db),
	moviedb: AsyncSession = Depends(movie_db),
):
	admin_service = AdminService(rssadb)
	movie_service = MovieService(moviedb)

	ers_movies = await movie_service.get_movies_with_emotions()
	movie_ids = [m.id for m in ers_movies]
	await admin_service.create_pre_shuffled_movie_list(movie_ids, 'ers', seed)

	return True
