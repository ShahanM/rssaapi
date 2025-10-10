"""
----
File: rspc.py
Project: RS:SA Recommender System (Clemson University)
Created Date: Tuesday, 26th August 2025
Author: Mehtab 'Shahan' Iqbal
Affiliation: Clemson University
----
Last Modified: Friday, 10th October 2025 2:54:36 am
Modified By: Mehtab 'Shahan' Iqbal (mehtabi@clemson.edu)
----
Copyright (c) 2025 Clemson University
License: MIT License (See LICENSE.md)
# SPDX-License-Identifier: MIT License
"""

import numpy as np
from lenskit import score
from lenskit.data import RecQuery

from data.schemas.participant_response_schemas import MovieLensRatingSchema

from .common import RSSABase, get_user_feature_vector


class PreferenceCommunity(RSSABase):
    def __init__(self, model_path: str, item_popularity, ave_item_score, data_path: str):
        super().__init__(model_path, item_popularity, ave_item_score)
        self.data_path = data_path

    def get_advisors_with_profile(self, ratings: list[MovieLensRatingSchema], user_id, num_rec=10) -> dict:
        rated_items = np.array([np.int64(rating.item_id) for rating in ratings])

        user_features = get_user_feature_vector(self.pipeline, ratings)

        # FIXME - parameterize
        distance_method = 'cosine'
        numNeighbors = 200

        # Returns the top 200 neighbors sorted in ascending order of distance
        neighbors = self._find_nearest_neighbors_annoy(new_user_vector=user_features, num_neighbors=numNeighbors)
        neighbors = neighbors[:num_rec]

        advisors = {}
        for neighbor in neighbors:
            advisor = {'id': neighbor, 'recommendation': str, 'profile_top': list}
            query = RecQuery(user_id=neighbor)
            user_implicit_preds = score(self.pipeline, query, self.items)

            preds = user_implicit_preds.to_df().reset_index()
            print(preds.head())
            preds.columns = ['index', 'item', 'score']

            preds = preds.sort_values(by='score', ascending=False).head(200)
            preds_without_rated = preds[~preds['item'].isin(rated_items)]
            pick_one_random = preds_without_rated.sample(1)
            advisor['recommendation'] = pick_one_random['item'].values[0]
            advisor['profile_top'] = preds.head(num_rec)['item'].tolist()
            advisors[neighbor] = advisor

        return advisors
