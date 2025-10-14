"""
----
File: common.py
Project: RS:SA Recommender System (Clemson University)
Created Date: Friday, 1st September 2023
Author: Mehtab 'Shahan' Iqbal
Affiliation: Clemson University
----
Last Modified: Tuesday, 14th October 2025 1:39:57 pm
Modified By: Mehtab 'Shahan' Iqbal (mehtabi@clemson.edu)
----
Copyright (c) 2025 Clemson University
License: MIT License (See LICENSE.md)
# SPDX-License-Identifier: MIT License
"""

from typing import cast

import numpy as np
import pandas as pd
from lenskit import predict
from lenskit.als import ALSBase
from lenskit.data import ItemList, RecQuery
from lenskit.pipeline import Pipeline
from lenskit.pipeline.nodes import ComponentInstanceNode

from data.schemas.participant_response_schemas import MovieLensRatingSchema
from services.recommenders.asset_loader import ModelAssetBundle


class RSSABase:
    def __init__(self, asset_bundle: ModelAssetBundle):
        self.pipeline: Pipeline = asset_bundle.pipeline
        self.scorer: ALSBase = asset_bundle.scorer

        self.annoy_index = asset_bundle.annoy_index
        self.user_map_lookup = asset_bundle.user_map_lookup

        self.history_lookup_map: pd.Series = asset_bundle.history_lookup_map
        self.item_popularity: pd.DataFrame = asset_bundle.item_popularity
        self.ave_item_score: pd.DataFrame = asset_bundle.ave_item_score
        self.items = self.item_popularity.item.unique()

    def _find_nearest_neighbors_annoy(self, new_user_vector: np.ndarray, num_neighbors: int) -> list[int]:
        """
        Finds K nearest neighbors using the pre-built Annoy index over the P matrix.

        Args:
            new_user_vector (np.ndarray): The projected 1D vector (q_u) of the new user.
            num_neighbors (int): The number of neighbors (K) to retrieve.

        Returns:
            list[str]: A list of external ids of the K neighbors.
        """
        internal_ids: list[int] = self.annoy_index.get_nns_by_vector(
            new_user_vector, num_neighbors, include_distances=False
        )

        external_ids: list[int] = [self.user_map_lookup[i] for i in internal_ids]

        return external_ids

    def _calculate_neighborhood_average(self, neighbor_ids: list[int], target_item: int, min_ratings: int = 1):
        """
        Calculates the average observed rating for a target item among the K neighbors
        using the in-memory history map.
        """

        ratings = []
        for user_id in neighbor_ids:
            # Lookup the neighbor's history (O(1) operation)
            history_tuples = self.history_lookup_map.get(user_id)

            if history_tuples:
                for item_id, rating in history_tuples:
                    if str(item_id) == str(target_item):
                        ratings.append(rating)
                        break

        if len(ratings) < min_ratings:
            return None

        return np.mean(ratings)

    def _get_target_item_factors(self, item_ids: list[int]) -> tuple[np.ndarray, list]:
        """
        Retrieves the Q (item factor) matrix subset corresponding to the list of item UUIDs.

        Args:
            item_uuids (list[str]): The list of external item IDs (UUIDs) to retrieve.

        Returns:
            np.ndarray: The sliced Q matrix (N_target_items x F_features).
        """

        item_vocab = self.scorer.items_

        # This returns an array of integer indices, with -1 for Out-of-Vocabulary (OOV) items.
        item_codes_full = item_vocab.numbers(item_ids, missing='negative')

        # Filter out OOV items (where code is -1)
        valid_mask = np.greater_equal(item_codes_full, 0)
        target_item_codes = item_codes_full[valid_mask]

        # Access the full Item Factor Matrix (Q matrix)
        Q_full_tensor = self.scorer.item_features_
        Q_full_numpy = Q_full_tensor.cpu().detach().numpy()

        # Subset the Q Matrix using the internal codes
        Q_target_slice = Q_full_numpy[target_item_codes, :]

        valid_item_ids = np.array(item_ids)[valid_mask].tolist()

        return Q_target_slice, valid_item_ids

    def _predict(self, user_id: str, ratings: list[MovieLensRatingSchema]) -> pd.DataFrame:
        """
        Generates predictions for a new (out-of-sample) user using the trained LensKit Pipeline.

        Args:
            model (Pipeline): The trained pipeline object loaded from disk.
            all_items_df (pd.DataFrame): DataFrame containing all candidate items.
            user_id (str): The new user's UUID (external ID).
            ratings (pd.Series): The new user's interaction history, indexed by item ID.

        Returns:
            pd.DataFrame: DataFrame containing item and score columns.
        """
        user_history_itemlist = self._ratings_to_item_list(ratings)
        query = RecQuery(user_id=user_id, user_items=user_history_itemlist)
        als_preds_il = predict(self.pipeline, query, items=self.items)
        als_preds = als_preds_il.to_df()

        print('als_preds: ', als_preds, len(als_preds))
        return als_preds

    def predict_discounted(
        self,
        userid: str,
        ratings: list[MovieLensRatingSchema],
        factor: int,
        coeff: float = 0.5,
    ) -> pd.DataFrame:
        """Predict the ratings for the new items for the live user.
        Discount the score of the items based on their popularity and
        compute the RSSA score.

        Args:
            model (Pipeline): The trained pipeline object loaded from disk.
            item_popularity (pd.DataFrame): ['item', 'count', 'rank']
            userid (str): User ID of the live user
            new_ratings (pd.Series): New ratings of the live user indexed by item ID
            factor (int): Number of items to be considered for discounting. Typically,
                it the order of magnitude of the number of items in the dataset.
                coeff (float): Discounting coefficient. Default value is 0.5.

        Returns:
            pd.DataFrame: ['item', 'score', 'count', 'rank', 'discounted_score']
                The dataframe is sorted by the discounted_score in descending order.
        """
        als_preds = self._predict(userid, ratings)

        als_preds = pd.merge(als_preds, self.item_popularity, left_on='item_id', right_on='item')
        als_preds['discounted_score'] = als_preds['score'] - coeff * (als_preds['count'] / factor)

        als_preds.sort_values(by='discounted_score', ascending=False, inplace=True)

        return als_preds

    def _ratings_to_item_list(self, ratings: list[MovieLensRatingSchema]) -> ItemList:
        data = [{'item_id': r.item_id, 'rating': float(r.rating)} for r in ratings]
        ratings_df = pd.DataFrame(data)
        scorer = self.scorer
        item_vocab = scorer.items_
        item_numbers_array = item_vocab.numbers(ratings_df['item_id'].to_numpy(), missing='negative')
        ratings_df['item_num'] = item_numbers_array
        user_history_itemlist = ItemList.from_df(ratings_df)

        return user_history_itemlist

    def get_user_feature_vector(self, ratings: list[MovieLensRatingSchema]) -> np.ndarray:
        """
        Extracts the new user's latent feature vector (q_u)
        using the Scorer's public new_user_embedding method.

        Args:
            pipeline (Pipeline): The trained pipeline object.
            ratings (pd.Series): The new user's ratings history (indexed by item ID).

        Returns:
            np.ndarray: The projected user feature vector (q_u).
        """

        user_history_itemlist = self._ratings_to_item_list(ratings)
        user_vector_tuple = self.scorer.new_user_embedding(None, user_history_itemlist)
        user_tensor = user_vector_tuple[0]
        user_vector_numpy = user_tensor.cpu().detach().numpy()

        return user_vector_numpy.flatten()

    @classmethod
    def get_scorer_from_pipeline(cls, pipeline: Pipeline) -> ALSBase:
        """
        Extracts the trained Scorer instance (ALSBase) from a Pipeine.

        Args:
            pipeline (Pipeline): The trained pipeline object

        Returns:
            ALSBase: A dervative of the ALSBase class.
        """
        pipeline_component: ComponentInstanceNode = cast(ComponentInstanceNode, pipeline.node('scorer'))
        scorer: ALSBase = cast(ALSBase, pipeline_component.component)

        return scorer


def scale_value(value, new_min, new_max, cur_min, cur_max):
    new_range = new_max - new_min
    cur_range = cur_max - cur_min
    new_value = new_range * (value - cur_min) / cur_range + new_min
    return new_value
