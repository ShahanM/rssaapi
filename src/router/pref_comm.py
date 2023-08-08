from fastapi import APIRouter, Depends
from util.docs_metadata import TagsMetadataEnum as Tags
from typing import List
from data.models.schema.advisorschema import *
from compute.iers import IERSCompute
from compute.utils import get_rating_data_path, get_iers_data, get_iers_model_path
from compute.rspc import RSSAPrefCommunity
from sqlalchemy.orm import Session
from data.moviedatabase import SessionLocal
from data.models.schema.movieschema import *
from data.movies import *
from collections import Counter, defaultdict

router = APIRouter()

rssa_pref_comm = RSSAPrefCommunity(get_rating_data_path())

iers_item_pop, iersg20 = get_iers_data()
iers_model_path = get_iers_model_path()
iersalgs = IERSCompute(iers_model_path, iers_item_pop, iersg20)

# Dependency
def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
@router.post("/prefComm/advisors/", response_model=List[AdvisorSchema], tags=[Tags.pref_comm])
async def get_advisor(rated_movies: PrefCommRatingSchema, \
	db: Session = Depends(get_db)):

	advisors = []
	
	recs = iersalgs.predict_topN(rated_movies.ratings, \
			rated_movies.user_id, rated_movies.num_rec)
	print(recs)

	recmovies = get_movies_by_ids(db, recs)

	for advid, rec in enumerate(recmovies, 1):
		advisor_data = rssa_pref_comm.get_advisor_profile(rec.movie_id)

		top_rated = advisor_data['top_rated']
		least_rated = advisor_data['least_rated']

		topmovies = get_movies_by_ids(db, top_rated)
		genredict = defaultdict(int)
		top_ten_genre = []
		for i, movie in enumerate(topmovies, 1):
			genres = movie.genre.split('|')
			if i <= 10:
				top_ten_genre.extend(genres)
			for genre in genres:
				genredict[genre] += 1

		most_common_genre = max(genredict, key=lambda key: genredict[key])
		toprated = Counter(top_ten_genre).most_common(1)
		
		bottommovies = get_movies_by_ids(db, least_rated)
		genredict2 = defaultdict(int)
		for movie in bottommovies:
			genres = movie.genre.split('|')
			for genre in genres:
				genredict2[genre] += 1

		least_common_genre = max(genredict2, key=lambda key: genredict2[key])

		likesdetail = get_ers_movie(db, advisor_data['favorite_movie'])
		dlikedetail = get_ers_movie(db, advisor_data['least_favorite_movie'])
		advisor_profile = AdvisorProfileSchema(\
			likes=f'{likesdetail.title} ({likesdetail.year})', \
			dislikes=f'{dlikedetail.title} ({dlikedetail.year})',\
			most_rated_genre=most_common_genre, \
			genretopten=toprated[0][0], \
			genre_with_least_rating=least_common_genre)
		advisor = AdvisorSchema(id=advid, \
					movie_id=rec.movie_id,
					name=rec.title, year=rec.year, \
					ave_rating=rec.ave_rating, genre=rec.genre, \
					director=rec.director, cast=rec.cast, \
					description=rec.description, poster=rec.poster, \
					emotions=None, poster_identifier=rec.poster_identifier, \
					profile=advisor_profile,
					status="Pending")
		advisors.append(advisor)
	return advisors
