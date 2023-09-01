"""
This file contains the RSSA Preference Community (RSPC) algorithms.

@Author: Mehtab Iqbal (Shahan)
@Affiliation: School of Computing, Clemson University
"""

import pandas as pd

class PreferenceCommunity:
	def __init__(self, data_path: str):
		self.data_path = data_path
	
# 	schema_dic = {
# 	'favorite_movie': int,
# 	'most_rated_genre': str,
# 	'least_favorite_movie': int,
# 	'least_rated_genre': str
# }

	def get_advisor_profile(self, movie_id: int) -> dict:
		return self.__build_advisor_profile(movie_id)

	def __build_advisor_profile(self, movie_id: int) -> dict:
		# g20_df = pd.read_csv('ieRS_ratings_g20.csv')
		rating_data = pd.read_csv(self.data_path)
		users = set(rating_data[rating_data['movie_id'] == movie_id]['user_id'].tolist())

		# Get the users who rated the movie with 5.0
		ratings_gt5 = rating_data[rating_data['user_id'].isin(users)\
						& (rating_data['rating'] == 5.0)
						& (rating_data['movie_id'] != movie_id)]
		
		top_movies = ratings_gt5.groupby('movie_id').size()\
						.reset_index(name='counts')\
						.sort_values('counts', ascending=False)
		q3 = top_movies['counts'].quantile(0.75)
		top_movies = top_movies[top_movies['counts'] > q3]

		fav_movie = top_movies['movie_id'].tolist()[0]

		# Get the 75th percentile of the top movies from the database
		# to get the most rated genre
		# get_movies_from_database(top_movies['movie_id'].tolist())

		# Get the users who rated the movie with 1.0
		ratings_lt2 = rating_data[rating_data['user_id'].isin(users)\
						& (rating_data['rating'] == 1.0)
						& (rating_data['movie_id'] != movie_id)]

		least_movies = ratings_lt2.groupby('movie_id')\
						.size().reset_index(name='counts')\
						.sort_values('counts', ascending=False)
		q3 = least_movies['counts'].quantile(0.75)
		least_movies = least_movies[least_movies['counts'] > q3]

		least_fav_movie = least_movies['movie_id'].tolist()[0]

		# Get the 75th percentile of the least movies from the database
		# to get the least rated genre
		# get_movies_from_database(least_movies['movie_id'].tolist())


		return {
			'favorite_movie': fav_movie,
			'least_favorite_movie': least_fav_movie,
			'top_rated': top_movies['movie_id'].tolist(),
			'least_rated': least_movies['movie_id'].tolist()
		}