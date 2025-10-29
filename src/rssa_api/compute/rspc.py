"""
This file contains the RSSA Preference Community (RSPC) algorithms.

@Author: Mehtab "Shahan" Iqbal
@Affiliation: School of Computing, Clemson University
"""

from typing import List

import numpy as np
import pandas as pd

from rssa_api.data.schemas.participant_response_schemas import MovieLensRatingSchema, RatedItemBaseSchema
from rssa_api.data.schemas.preferences_schemas import RatedItemSchema

from .common import RSSABase, get_user_feature_from_implicitMF


class PreferenceCommunity(RSSABase):
    def __init__(self, model_path: str, item_popularity, ave_item_score, data_path: str):
        super().__init__(model_path, item_popularity, ave_item_score)
        self.data_path = data_path

        # 	schema_dic = {
        # 	'favorite_movie': int,
        # 	'most_rated_genre': str,
        # 	'least_favorite_movie': int,
        # 	'least_rated_genre': str
        # }

    def get_advisors_with_profile(self, ratings: List[MovieLensRatingSchema], user_id, num_rec=10) -> dict:
        _ratings = pd.Series([rating.rating for rating in ratings])
        rated_items = np.array([np.int64(rating.item_id) for rating in ratings])

        umat = self.model.user_features_
        users = self.model.user_index_

        user_features = get_user_feature_from_implicitMF(self.model, _ratings)

        # FIXME - parameterize
        distance_method = 'cosine'
        numNeighbors = 200

        # Returns the top 200 neighbors sorted in ascending order of distance
        neighbors = RSSABase._find_neighbors(self, umat, users, user_features, distance_method, numNeighbors)

        neighbors = neighbors.head(num_rec)
        neighbors = neighbors['user'].tolist()

        advisors = {}
        # advisor_preds = {}
        # max_rated_item = max(ratings, key=lambda x: x.rating)
        # print('Max rated item: ', max_rated_item)
        # max_rated_items = [rating.item_id for rating in ratings if rating.rating == max_rated_item.rating]
        # print('Max rated items: ', max_rated_items)

        # mri_idx = self.item_popularity[self.item_popularity['item'].isin(max_rated_items)]
        # mri_features = self.model.item_features_[mri_idx.index]

        for neighbor in neighbors:
            advisor = {'id': neighbor}
            preds = self.model.predict_for_user(neighbor, self.items)

            preds = preds.to_frame().reset_index()
            preds.columns = ['item', 'score']

            preds = preds.sort_values(by='score', ascending=False).head(200)
            preds_without_rated = preds[~preds['item'].isin(rated_items)]
            pick_one_random = preds_without_rated.sample(1)
            advisor['recommendation'] = pick_one_random['item'].values[0]
            # adv_item_features = self.model.item_features_[preds_without_rated.index]
            # itm_dist_pair = []
            # for i in range(mri_features.shape[0]):
            # 	for j in range(adv_item_features.shape[0]):
            # 		dist = cosine(mri_features[i, ], adv_item_features[j, ])
            # 		itm_dist_pair.append((max_rated_items[i], preds_without_rated.iloc[j]['item'], dist))
            advisor['profile_top'] = preds.head(num_rec)['item'].tolist()
            advisors[neighbor] = advisor

            # closest = sorted(itm_dist_pair, key=lambda x: x[2])
            # print('Closest: ', closest[:5])

            # TODO: find the movie that advisor would recommend
            # Options:
            # 1. item_features_[[top 200 movies for advisor], ]
            # -> distance measure with item_features_[[rated_items], ]
            # -> return the closest as a recommendation

        return advisors

    def get_advisor_profile(self, movie_id: int) -> dict:
        return self.__build_advisor_profile(movie_id)

    def __build_advisor_profile(self, movie_id: int) -> dict:
        # g20_df = pd.read_csv('ieRS_ratings_g20.csv')
        rating_data = pd.read_csv(self.data_path)
        users = set(rating_data[rating_data['movie_id'] == movie_id]['user_id'].tolist())

        # Get the users who rated the movie with 5.0
        ratings_gt5 = rating_data[
            rating_data['user_id'].isin(users) & (rating_data['rating'] == 5.0) & (rating_data['movie_id'] != movie_id)
        ]

        top_movies = (
            ratings_gt5.groupby('movie_id').size().reset_index(name='counts').sort_values('counts', ascending=False)
        )
        q3 = top_movies['counts'].quantile(0.75)
        top_movies = top_movies[top_movies['counts'] > q3]

        fav_movie = top_movies['movie_id'].tolist()[0]

        # Get the 75th percentile of the top movies from the database
        # to get the most rated genre
        # get_movies_from_database(top_movies['movie_id'].tolist())

        # Get the users who rated the movie with 1.0
        ratings_lt2 = rating_data[
            rating_data['user_id'].isin(users) & (rating_data['rating'] == 1.0) & (rating_data['movie_id'] != movie_id)
        ]

        least_movies = (
            ratings_lt2.groupby('movie_id').size().reset_index(name='counts').sort_values('counts', ascending=False)
        )
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
            'least_rated': least_movies['movie_id'].tolist(),
        }
