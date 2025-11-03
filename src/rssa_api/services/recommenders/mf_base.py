"""
----
File: mf_base.py
Project: RS:SA Recommender System (Clemson University)
Created Date: Friday, 1st September 2023
Author: Mehtab 'Shahan' Iqbal
Affiliation: Clemson University
----
Last Modified: Sunday, 2nd November 2025 1:35:02 am
Modified By: Mehtab 'Shahan' Iqbal (mehtabi@clemson.edu)
----
Copyright (c) 2025 Clemson University
License: MIT License (See LICENSE.md)
# SPDX-License-Identifier: MIT License
"""

from typing import Optional, Union, cast

import binpickle
import numpy as np
import pandas as pd
from annoy import AnnoyIndex
from lenskit.algorithms import als
from lenskit.algorithms.mf_common import MFPredictor

from rssa_api.core.config import MODELS_DIR
from rssa_api.data.schemas.participant_response_schemas import MovieLensRatingSchema

MFModelType = Union[als.BiasedMF, als.ImplicitMF]


class RSSABase:
    def __init__(self, model_folder: str):
        self.path = MODELS_DIR / model_folder
        self.item_popularity = pd.read_csv(self.path / 'item_popularity.csv')
        self.ave_item_score = pd.read_csv(self.path / 'averaged_item_score.csv')

        mf_model: MFPredictor = self._load_model_asset()
        model_instance: Optional[MFModelType] = self._get_typed_model_instance(mf_model)
        if model_instance is None:
            raise RuntimeError('Model was not loaded properly.')
        self.model: MFModelType = model_instance
        self.items = self.item_popularity.item.unique()

    def _load_model_asset(self):
        return binpickle.load(f'{self.path}/model.bpk')

    def _get_typed_model_instance(self, model: MFPredictor) -> Optional[Union[als.BiasedMF, als.ImplicitMF]]:
        if isinstance(model, als.BiasedMF):
            model = cast(als.BiasedMF, model)
        elif isinstance(model, als.ImplicitMF):
            model = cast(als.ImplicitMF, model)
        else:
            return None
        return model

    def find_nearest_neighbors_annoy(self, new_user_vector: np.ndarray, num_neighbors: int) -> list[int]:
        """
        Finds K nearest neighbors using the pre-built Annoy index over the P matrix.

        Args:
            new_user_vector: The projected 1D vector (q_u) of the new user.
            num_neighbors: The number of neighbors (K) to retrieve.

        Returns:
            A list of external ids of the K neighbors.
        """
        annoy_index, user_map_lookup = self._load_annoy_assets_asset()
        internal_ids: list[int] = annoy_index.get_nns_by_vector(new_user_vector, num_neighbors, include_distances=False)
        del annoy_index

        external_ids: list[int] = [user_map_lookup[i] for i in internal_ids]
        del user_map_lookup

        return external_ids

    def _load_history_lookup_asset(self) -> pd.Series:
        """Loads the compact user history Parquet file and converts it to a dict/Series for quick lookup."""
        history_path = f'{self.path}/user_history_lookup.parquet'

        history_df = pd.read_parquet(history_path)

        # Convert the DataFrame back to a Series indexed by user ID for O(1) lookup speed
        # The Series values are the list of (item_id, rating) tuples
        return history_df.set_index('user')['history_tuples']

    def _load_annoy_assets_asset(self):
        """Loads the pre-built Annoy index and the ID mapping table."""

        annoy_index_path = f'{self.path}/annoy_index'
        user_map_path = f'{annoy_index_path}_map.csv'

        user_feature_vector = self.model.user_features_
        if user_feature_vector is None:
            raise RuntimeError()

        dims = user_feature_vector.shape[1]

        index = AnnoyIndex(dims, 'angular')
        try:
            index.load(annoy_index_path)
        except Exception as e:
            raise FileNotFoundError(
                f'Annoy index file not found at {annoy_index_path}. Did you run training with --cluster_index?'
            ) from e

        # Load User Map (Annoy ID -> user ID)
        user_map_df = pd.read_csv(user_map_path, index_col=0)

        # Convert the Series/DataFrame to a fast dictionary lookup (internal ID -> external ID)
        return index, user_map_df.iloc[:, 0].to_dict()

    def calculate_neighborhood_average(self, neighbor_ids: list[int], target_item: int, min_ratings: int = 1):
        """
        Calculates the average observed rating for a target item among the K neighbors
        using the in-memory history map.
        """
        history_lookup_map = self._load_history_lookup_asset()
        ratings = []
        for user_id in neighbor_ids:
            # Lookup the neighbor's history (O(1) operation)
            history_tuples = history_lookup_map.get(user_id)

            if history_tuples:
                for item_id, rating in history_tuples:
                    if str(item_id) == str(target_item):
                        ratings.append(rating)
                        break

        if len(ratings) < min_ratings:
            return None

        del history_lookup_map

        return np.mean(ratings)

    def get_target_item_factors(self, item_ids: list[int]) -> tuple[np.ndarray, list[int]]:
        """Retrieves the Q (item factor) matrix subset corresponding to the list of item UUIDs.

        Args:
            item_uuids (list[str]): The list of external item IDs (UUIDs) to retrieve.

        Returns:
            np.ndarray: The sliced Q matrix (N_target_items x F_features).
        """

        item_vocab = self.model.item_index_

        # This returns an array of integer indices, with -1 for Out-of-Vocabulary (OOV) items.
        item_codes_full = item_vocab.numbers(item_ids, missing='negative')

        # Filter out OOV items (where code is -1)
        valid_mask = np.greater_equal(item_codes_full, 0)
        target_item_codes = item_codes_full[valid_mask]

        # Access the full Item Factor Matrix (Q matrix)
        Q_full_numpy = self.model.item_features_
        # Q_full_numpy = Q_full_tensor.cpu().detach().numpy()

        # Subset the Q Matrix using the internal codes
        Q_target_slice = Q_full_numpy[target_item_codes, :]

        valid_item_ids = np.array(item_ids)[valid_mask].tolist()

        return Q_target_slice, valid_item_ids

    def predict(self, user_id: str, ratings: list[MovieLensRatingSchema]) -> pd.DataFrame:
        """Generates predictions for a new (out-of-sample) user using the trained LensKit Pipeline.

        Args:
            model (Pipeline): The trained pipeline object loaded from disk.
            all_items_df (pd.DataFrame): DataFrame containing all candidate items.
            user_id (str): The new user's UUID (external ID).
            ratings (pd.Series): The new user's interaction history, indexed by item ID.

        Returns:
            pd.DataFrame: DataFrame containing item and score columns.
        """
        rated_items = np.array([rating.item_id for rating in ratings], dtype=np.int32)
        new_ratings = pd.Series([rating.rating for rating in ratings], index=rated_items, dtype=np.float64)
        itemset = self.item_popularity.item.unique()
        als_preds = self.model.predict_for_user(user_id, itemset, new_ratings)

        als_preds_df = als_preds.to_frame().reset_index()
        als_preds_df.columns = ['item_id', 'score']

        return als_preds_df

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
        als_preds = self.predict(userid, ratings)

        als_preds = pd.merge(als_preds, self.item_popularity, left_on='item_id', right_on='item')
        als_preds['discounted_score'] = als_preds['score'] - coeff * (als_preds['count'] / factor)

        als_preds.sort_values(by='discounted_score', ascending=False, inplace=True)

        return als_preds

    def get_user_feature_vector(self, ratings: list[MovieLensRatingSchema]) -> Optional[np.ndarray]:
        """
        Extracts the new user's latent feature vector (q_u)
        using the Scorer's public new_user_embedding method.

        Args:
            pipeline (Pipeline): The trained pipeline object.
            ratings (pd.Series): The new user's ratings history (indexed by item ID).

        Returns:
            np.ndarray: The projected user feature vector (q_u).
        """
        rated_items = np.array([rating.item_id for rating in ratings], dtype=np.int32)
        new_ratings = pd.Series([rating.rating for rating in ratings], index=rated_items, dtype=np.float64)

        ri_idxes = self.model.item_index_.get_indexer_for(new_ratings.index)
        ri_good = ri_idxes >= 0
        ri_it = ri_idxes[ri_good]
        ri_val = new_ratings.values[ri_good]

        if isinstance(self.model, als.ImplicitMF):
            self.model = cast(als.ImplicitMF, self.model)
            ri_val *= self.model.weight
            return als._train_implicit_row_lu(ri_it, ri_val, self.model.item_features_, self.model.OtOr_)
        elif isinstance(self.model, als.BiasedMF):
            self.model = cast(als.BiasedMF, self.model)
            ureg = self.model.regularization
            return als._train_bias_row_lu(ri_it, ri_val, self.model.item_features_, ureg)

        return None


def scale_value(value, new_min, new_max, cur_min, cur_max):
    new_range = new_max - new_min
    cur_range = cur_max - cur_min
    new_value = new_range * (value - cur_min) / cur_range + new_min
    return new_value
