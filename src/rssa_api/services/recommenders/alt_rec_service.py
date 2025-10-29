"""
----
File: alt_rec_service.py
Project: RS:SA Recommender System (Clemson University)
Created Date: Monday, 13th October 2025
Author: Mehtab 'Shahan' Iqbal and Lijie Guo
Affiliation: Clemson University
----
Last Modified: Thursday, 16th October 2025 11:06:03 pm
Modified By: Mehtab 'Shahan' Iqbal (mehtabi@clemson.edu)
----
Copyright (c) 2025 Clemson University
License: MIT License (See LICENSE.md)
# SPDX-License-Identifier: MIT License
"""

import logging
import time
from typing import Literal, Union

import binpickle
import numpy as np
import pandas as pd
from lenskit.algorithms import als
from pydantic.dataclasses import dataclass

from rssa_api.core.config import MODELS_DIR
from rssa_api.data.schemas.participant_response_schemas import MovieLensRatingSchema
from rssa_api.services.recommenders.asset_loader import ModelAssetBundle

from .mf_base import RSSABase

log = logging.getLogger(__name__)


@dataclass
class Preference:
    """
    Represents a predicted or actual preference. `categories`
    is a list of classes that an item belongs to.
    """

    item_id: str
    categories: Union[Literal['top_n'], Literal['controversial'], Literal['hate'], Literal['hip'], Literal['no_clue']]


class AlternateRS(RSSABase):
    """
    Service for generating recommendations based on specific behavioral conditions
    (e.g., controversial, hip, hate) using advanced statistical analysis
    on model predictions.
    """

    # NOTE: The AlternateRS service currently uses the same IMPLICIT_MODEL_PATH
    # as the PrefComService, relying on shared asset loading.
    def __init__(self, model_folder: str):
        super().__init__(model_folder)

        self.discounting_factor = self.__init_discounting_factor(self.item_popularity)
        self.discounting_coefficient = 0.5  # FIXME: Should be loaded from a configuration source

        self.prediction_functions = {
            0: self.predict_user_top_n,
            1: self.predict_user_controversial_items,
            2: self.predict_user_hate_items,
            3: self.predict_user_hip_items,
            4: self.predict_user_no_clue_items,
        }

    def __init_discounting_factor(self, item_popularity):
        """
        Calculates the exponent factor used to scale down popularity counts.

        Args:
            item_popularity: DataFrame with ['item', 'count', 'rank_popular'].

        Returns:
            float: The scaling factor (power of 10).
        """
        max_count = item_popularity['count'].max()
        return 10 ** len(str(max_count))

    def get_condition_prediction(
        self, ratings: list[MovieLensRatingSchema], user_id: str, condition: int, num_rec: int
    ) -> list[str]:
        """
        Routes the request to the appropriate prediction method based on condition code.

        Args:
            ratings: List of rated item schemas from the new user.
            user_id: User UUID.
            condition: Integer code specifying the recommendation type (0-4).
            num_rec: Number of recommendations to return.

        Returns:
            list[str]: A list of recommended item IDs (strings).

        Raises:
            KeyError: If the condition code is invalid or missing a mapped function.
        """
        return self.prediction_functions[condition](ratings, user_id, num_rec)

    def get_predictions(self, ratings: list[MovieLensRatingSchema], user_id: str) -> pd.DataFrame:
        """
        Generates the user's predicted scores for all items, excluding items
        the user has already rated.

        Args:
            ratings: List of rated item schemas from the new user.
            user_id: User UUID.

        Returns:
            pd.DataFrame: DataFrame containing predictions ['item', 'score']
                        for unrated items.
        """

        rated_items = {r.item_id for r in ratings}
        _preds = self.predict_discounted(user_id, ratings, self.discounting_factor)

        return _preds[~_preds['item'].isin(rated_items)]

    def predict_user_top_n(self, ratings: list[MovieLensRatingSchema], user_id, n=10) -> list[int]:
        """
        Recommends the Top N highest predicted items (standard baseline).

        Args:
            ratings, user_id: User context.
            n: Number of recommendations.

        Returns:
            list[int]: Top N recommended item IDs.
        """
        top_n_discounted = self.get_predictions(ratings, user_id).head(n)

        return top_n_discounted['item'].astype(int).to_list()

    def predict_user_hate_items(self, ratings: list[MovieLensRatingSchema], user_id, n=10) -> list[int]:
        """
        Recommends items predicted high by the community average but low by the user
        (items the user will 'hate' relative to the general consensus).

        Args:
            ratings, user_id: User context.
            n: Number of recommendations.

        Returns:
            list[int]: Top N 'hate' item IDs.
        """
        preds = self.get_predictions(ratings, user_id)

        preds = pd.merge(preds, self.ave_item_score, how='left', on='item')
        preds['margin_discounted'] = preds['ave_discounted_score'] - preds['score']

        preds = preds.sort_values(by='margin_discounted', ascending=False).head(n)

        return preds['item'].astype(int).to_list()

    def predict_user_hip_items(self, ratings: list[MovieLensRatingSchema], user_id, n=10) -> list[int]:
        """
        Recommends 'hip' items (items with high predicted score but low popularity/count).

        Args:
            ratings, user_id: User context.
            n: Number of recommendations.

        Returns:
            list[int]: Top N 'hip' item IDs.
        """
        # Search over a larger initial pool (num_bs=1000)
        num_bs = 1000
        top_n = self.get_predictions(ratings, user_id).head(num_bs)

        # Filter: Highest Score + Lowest Count (Hip)
        # Sort ascending by count, keeping the top n items (least popular, highly predicted)
        hip_items = top_n.sort_values(by='count', ascending=True).head(n)

        return hip_items['item'].astype(int).to_list()

    def predict_user_no_clue_items(self, ratings: list[MovieLensRatingSchema], user_id, n=10) -> list[int]:
        """
        Recommends 'no clue' items (items with the highest prediction variance across
        resampled models, indicating high model uncertainty).

        Args:
            ratings, user_id: User context.
            n: Number of recommendations.

        Returns:
            list[int]: Top N 'no clue' item IDs.
        """

        resampled_df = self._high_std(user_id, ratings)
        rated_items = {r.item_id for r in ratings}
        resampled_df = resampled_df[~resampled_df['item'].isin(rated_items)]
        resampled_df = resampled_df.sort_values(by='std', ascending=False).head(n)

        return resampled_df['item'].astype(int).to_list()

    def predict_user_controversial_items(self, ratings: list[MovieLensRatingSchema], user_id, numRec=10) -> list[str]:
        """
        Recommends 'controversial' items (items with high variance in predicted scores
        among the K nearest neighbors, indicating high local disagreement).

        Args:
            ratings, user_id: User context.
            numRec: Number of recommendations.

        Returns:
            list[int]: Top N 'controversial' item IDs.
        """
        search_space_k = 20

        user_features = self.get_user_feature_vector(ratings)
        if user_features is None:
            return []
        annoy_index, user_map_lookup = self._load_annoy_assets_asset()
        rated_items = {r.item_id for r in ratings}
        neighborhood = annoy_index.get_nns_by_vector(user_features, search_space_k)
        del annoy_index
        variance = self._controversial(neighborhood, user_map_lookup)
        del user_map_lookup

        variance_wo_rated = variance[~variance['item_id'].isin(rated_items)]
        controversial_items = variance_wo_rated.sort_values(by='variance', ascending=False).head(numRec)

        return list(map(str, controversial_items['item_id']))

    def _high_std(self, user_id: str, ratings: list[MovieLensRatingSchema]):
        """
        Calculates model uncertainty (standard deviation of predicted scores)
        across 20 resampled Matrix Factorization models.

        Args:
            user_id: The UUID of the live user.
            new_ratings: The user's new ratings history for warm-start projection.

        Returns:
            pd.DataFrame: Items ranked by prediction standard deviation ('std').
        """
        all_resampled_df = pd.DataFrame(self.items, columns=['item'])
        rated_items = np.array([rating.item_id for rating in ratings], dtype=np.int32)
        new_ratings = pd.Series([rating.rating for rating in ratings], index=rated_items, dtype=np.float64)
        n_models = 20
        for i in range(1, n_models + 1):
            filename = MODELS_DIR / f'implicit_als_ml32m/resampled_model_{i}.bpk'
            model: als.ImplicitMF = binpickle.load(filename)
            items_in_sample = model.item_index_.to_numpy()
            resampled_preds = model.predict_for_user(user_id, items_in_sample, new_ratings)

            resampled_df = resampled_preds.to_frame().reset_index()
            col = f'score{i}'
            resampled_df.columns = ['item', col]

            all_resampled_df = pd.merge(all_resampled_df, resampled_df, how='left', on='item')
            del model  # we delete the loaded model to ensure there are no softlinks

        preds_only_df = all_resampled_df.drop(columns=['item']).apply(pd.to_numeric, errors='coerce')
        all_resampled_df['std'] = np.nanstd(preds_only_df, axis=1)
        all_items_std_df = all_resampled_df[['item', 'std']]
        all_items_std_df = pd.merge(all_items_std_df, self.item_popularity, how='left', on='item')

        return all_items_std_df

    def _controversial(self, neighborhood_annoy_ids: list[int], user_map_lookup: dict[int, int]):
        """
        Calculates the variance of predicted scores among the K nearest neighbors.

        Args:
            neighborhood_internal_codes: List of internal 0-based indices (Annoy IDs) of K neighbors.

        Returns:
            pd.DataFrame: Items ranked by prediction variance ('variance').
        """
        start = time.time()
        log.info(f'Starting vectorized calculation of variance for {len(neighborhood_annoy_ids)} neighbors...')
        external_neighbor_ids = [user_map_lookup.get(aid) for aid in neighborhood_annoy_ids]
        external_neighbor_ids = [uid for uid in external_neighbor_ids if uid is not None]
        try:
            internal_indices = np.arange(len(self.model.user_index_))
            external_internal_map = pd.Series(data=internal_indices, index=self.model.user_index_)
            internal_index_series = external_internal_map.reindex(external_neighbor_ids)
            model_internal_indices = internal_index_series.dropna().astype(int).values.tolist()
        except KeyError as e:
            log.error(f'Failed to find user from neighbor index: {e}')
            return pd.DataFrame(columns=['item_id', 'variance'])

        global_bias = getattr(self.model, 'global_bias', 0.0)
        user_features = self.model.user_features_
        item_features = self.model.item_features_
        item_index = self.model.item_index_

        if user_features is None:
            log.error('Model does not have user_features')
            return pd.DataFrame(columns=['item_id', 'variance'])

        neighbor_features = user_features[model_internal_indices, :]
        prediction_matrix = neighbor_features @ item_features.T
        prediction_matrix += global_bias  # implicit mf does not add the bias term so it's 0.0
        item_variance_vector = np.nanvar(prediction_matrix, axis=0)
        scores_df = pd.DataFrame({'item_id': item_index, 'variance': item_variance_vector})
        scores_df = pd.merge(scores_df, self.item_popularity, how='left', left_on='item_id', right_on='item').drop(
            columns=['item']
        )
        log.info(
            f'Time spent (vectorized controversial): {(time.time() - start):.4f}s. Calculated variance for {len(item_index)} items.'
        )

        return scores_df[['item_id', 'variance', 'count', 'rank_popular']]
