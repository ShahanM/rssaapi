"""
----
File: rspc.py
Project: RS:SA Recommender System (Clemson University)
Created Date: Tuesday, 26th August 2025
Author: Mehtab 'Shahan' Iqbal
Affiliation: Clemson University
----
Last Modified: Wednesday, 15th October 2025 9:05:04 pm
Modified By: Mehtab 'Shahan' Iqbal (mehtabi@clemson.edu)
----
Copyright (c) 2025 Clemson University
License: MIT License (See LICENSE.md)
# SPDX-License-Identifier: MIT License
"""

from data.schemas.participant_response_schemas import MovieLensRatingSchema
from services.recommenders.asset_loader import ModelAssetBundle

from .mf_base import RSSABase


class PreferenceCommunity(RSSABase):
    def __init__(self, asset_bundle: ModelAssetBundle):
        super().__init__(asset_bundle)

    def get_advisors_with_profile(self, ratings: list[MovieLensRatingSchema], num_rec=10) -> dict:
        """
        Identifies the K nearest latent neighbors (advisors) to the new user and
        extracts a diverse recommendation and top profile from each neighbor.

        Args:
            ratings (List[MovieLensRatingSchema]): New user's 10 warm-start ratings.
            num_rec (int): The final number of unique neighbors/advisors to return (K in the K-NN).

        Returns:
            dict: A dictionary mapping advisor UUIDs to their profile and unique recommendation.
        """
        user_features = self.get_user_feature_vector(ratings)
        if user_features is None:
            raise RuntimeError('Could not load user features from trained model')

        search_space_k = 200
        all_neighbors_ids = self._find_nearest_neighbors_annoy(
            new_user_vector=user_features, num_neighbors=search_space_k
        )
        final_advisors_ids = all_neighbors_ids[:num_rec]
        rated_items = {r.item_id for r in ratings}

        advisors = {}
        for neighbor_id in final_advisors_ids:
            advisor = {'id': neighbor_id, 'recommendation': None, 'profile_top': []}
            user_implicit_preds = self.model.predict_for_user(neighbor_id, self.items)
            preds_df = user_implicit_preds.to_frame().reset_index()
            preds_df.columns = ['item_id', 'score']
            preds_df = preds_df.sort_values(by='score', ascending=False)
            preds_without_rated = preds_df[~preds_df['item_id'].isin(rated_items)]

            if not preds_without_rated.empty:
                pick_one_random = preds_without_rated.sample(1)
                advisor['recommendation'] = pick_one_random['item_id'].values[0]

            advisor['profile_top'] = preds_df.head(num_rec)['item_id'].tolist()
            advisors[neighbor_id] = advisor

        return advisors
