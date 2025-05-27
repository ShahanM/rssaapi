import pandas as pd

g20_df = pd.read_csv('ieRS_ratings_g20.csv')
# print(g20_df.head())

schema_dic = {
	'favorite_movie': int,
	'most_rated_genre': str,
	'least_favorite_movie': int,
	'least_rated_genre': str
}

def __build_advisor_profile(df: pd.DataFrame, movie_id: int, top_n: int) -> dict:
	users = set(df[df['movie_id'] == movie_id]['user_id'].tolist())

	# Get the users who rated the movie with 5.0
	ratings_gt5 = df[df['user_id'].isin(users) & (df['rating'] == 5.0) & (df['movie_id'] != movie_id)]

	top_movies = ratings_gt5.groupby('movie_id').size().reset_index(name='counts').sort_values('counts', ascending=False)
	q3 = top_movies['counts'].quantile(0.75)
	top_movies = top_movies[top_movies['counts'] > q3]

	fav_movie = top_movies['movie_id'].tolist()[0]

	# Get the 75th percentile of the top movies from the database
	# to get the most rated genre
	# get_movies_from_database(top_movies['movie_id'].tolist())

	# Get the users who rated the movie with 1.0
	ratings_lt2 = df[df['user_id'].isin(users) & (df['rating'] == 1.0) & (df['movie_id'] != movie_id)]

	least_movies = ratings_lt2.groupby('movie_id').size().reset_index(name='counts').sort_values('counts', ascending=False)
	q3 = least_movies['counts'].quantile(0.75)
	least_movies = least_movies[least_movies['counts'] > q3]

	least_fav_movie = least_movies['movie_id'].tolist()[0]

	# Get the 75th percentile of the least movies from the database
	# to get the least rated genre
	# get_movies_from_database(least_movies['movie_id'].tolist())




rated_296 = g20_df[(g20_df['movie_id'] == 296) & (g20_df['rating'] == 5.0)]
# print(rated_296.head(), '\n', rated_296.shape)

users_296 = rated_296['user_id'].tolist()
user_set = set(rated_296['user_id'].tolist())
user_total_ratings_gt_3 = g20_df[g20_df['user_id'].isin(user_set) & (g20_df['rating'] == 5.0) & (g20_df['movie_id'] != 296)]

movie_buckets = user_total_ratings_gt_3.groupby('movie_id').size().reset_index(name='counts').sort_values('counts', ascending=False)
q3 = movie_buckets['counts'].quantile(0.75)
movie_buckets = movie_buckets[movie_buckets['counts'] > q3]
print(movie_buckets.shape)
print(movie_buckets.sort_values('counts', ascending=True).head(10))

# print(user_total_ratings_gt_3[user_total_ratings_gt_3['movie_id'] != 296].shape)

# print(user_total_ratings_gt_3.assign(freq=user_total_ratings_gt_3.groupby('movie_id')['movie_id'].transform('count'))\
#     .sort_values(by=['freq'],ascending=[False]).head())

# print(user_total_ratings_gt_3.groupby('movie_id').size().reset_index(name='counts').sort_values('counts', ascending=True).head(10))
# print(user_total_ratings_gt_3[user_total_ratings_gt_3['movie_id'] == 593].head(10))

# print(user_total_ratings_gt_3.head())
# user_total_ratings_gt_3['movie_id_count'] = user_total_ratings_gt_3.groupby('movie_id')['movie_id'].transform(pd.Series.value_counts)
# user_total_ratings_gt_3.sort_values('movie_id_count', inplace=True, ascending=False)
# print('df sorted: \n{}'.format(user_total_ratings_gt_3.head()))
# print(user_total_ratings_gt_3.sort_values('movie_id_count', ascending=False).head())
# print(user_total_ratings_gt_3.groupby('movie_id').count().head())
# each_user_total_ratings_gt_3 = user_total_ratings_gt_3.groupby('user_id').count()
# print(sum(each_user_total_ratings_gt_3['movie_id'].tolist())/each_user_total_ratings_gt_3.shape[0])
# for user in users_296:
	# user_set = g20_df[g20_df['user_id'] == user]
