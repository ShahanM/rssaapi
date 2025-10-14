"""
----
File: alt_rec_service.py
Project: RS:SA Recommender System (Clemson University)
Created Date: Monday, 13th October 2025
Author: Mehtab 'Shahan' Iqbal and Lijie Guo
Affiliation: Clemson University
----
Last Modified: Tuesday, 14th October 2025 1:35:43 pm
Modified By: Mehtab 'Shahan' Iqbal (mehtabi@clemson.edu)
----
Copyright (c) 2025 Clemson University
License: MIT License (See LICENSE.md)
# SPDX-License-Identifier: MIT License
"""

import logging
from typing import Literal

import binpickle
import numpy as np
import pandas as pd
from lenskit import Pipeline, predict, score
from lenskit.data import ItemList, RecQuery
from pydantic.dataclasses import dataclass

from core.config import MODELS_DIR
from data.schemas.participant_response_schemas import MovieLensRatingSchema
from services.recommenders.asset_loader import ModelAssetBundle

from .mf_base import RSSABase

log = logging.getLogger(__name__)


@dataclass
class Preference:
    """
    Represents a predicted or actual preference. `categories`
    is a list of classes that an item belongs to.
    """

    item_id: str
    categories: Literal['top_n'] | Literal['controversial'] | Literal['hate'] | Literal['hip'] | Literal['no_clue']


class AlternateRS(RSSABase):
    """
    Service for generating recommendations based on specific behavioral conditions
    (e.g., controversial, hip, hate) using advanced statistical analysis
    on model predictions.
    """

    # NOTE: The AlternateRS service currently uses the same IMPLICIT_MODEL_PATH
    # as the PrefComService, relying on shared asset loading.
    def __init__(self, asset_bundle: ModelAssetBundle):
        super().__init__(asset_bundle)

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

        rated_items = {r.item_id for r in ratings}
        neighborhood = self.annoy_index.get_nns_by_vector(user_features, search_space_k)

        variance = self._controversial(neighborhood)

        variance_wo_rated = variance[~variance['item'].isin(rated_items)]
        controversial_items = variance_wo_rated.sort_values(by='variance', ascending=False).head(numRec)

        return list(map(str, controversial_items['item']))

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

        n_models = 20
        for i in range(1, n_models + 1):
            filename = MODELS_DIR / f'ml32m/resampled_model_{i}.bpk'
            pipeline: Pipeline = binpickle.load(filename)
            scorer = RSSABase.get_scorer_from_pipeline(pipeline)
            data = [{'item_id': r.item_id, 'rating': float(r.rating)} for r in ratings]
            ratings_df = pd.DataFrame(data)
            item_ids_to_check = ratings_df['item_id'].to_numpy()

            # Safe lookup (using the model's current vocabulary)
            item_vocab = scorer.items_
            item_codes_full = item_vocab.numbers(item_ids_to_check, missing='negative')  # <-- SAFE

            # Filter the ItemList: Only proceed with known items
            valid_mask = np.greater_equal(item_codes_full, 0)

            # If the list is empty after filtering, skip this iteration entirely
            if not np.any(valid_mask):
                continue

            # We only want to create the ItemList from known items
            filtered_ratings_df = ratings_df[valid_mask].copy()
            user_history_itemlist = ItemList.from_df(filtered_ratings_df)  # <-- SAFE INPUT

            query = RecQuery(user_id=user_id, user_items=user_history_itemlist)
            als_preds_il = predict(pipeline, query, items=item_vocab.ids())
            als_preds = als_preds_il.to_df()
            col = f'score{i}'
            als_preds.columns = ['item', col]

            all_resampled_df = pd.merge(all_resampled_df, als_preds, how='left', on='item')
            del pipeline  # we delete the loaded model to ensure there are no softlinks

        preds_only_df = all_resampled_df.drop(columns=['item']).apply(pd.to_numeric, errors='coerce')
        all_resampled_df['std'] = np.nanstd(preds_only_df, axis=1)
        all_items_std_df = all_resampled_df[['item', 'std']]
        all_items_std_df = pd.merge(all_items_std_df, self.item_popularity, how='left', on='item')

        return all_items_std_df

    def _controversial(self, neighborhood):
        """
        Calculates the variance of predicted scores among the K nearest neighbors.

        Args:
            neighborhood_internal_codes: List of internal 0-based indices (Annoy IDs) of K neighbors.

        Returns:
            pd.DataFrame: Items ranked by prediction variance ('variance').
        """
        scores_df = pd.DataFrame(list(self.items), columns=['item'])
        user_map_lookup = self.user_map_lookup

        # Build the Prediction Matrix (Item Rows vs. Neighbor Columns)
        for internal_id in neighborhood:
            neighbor_id = user_map_lookup.get(internal_id)
            if neighbor_id is None:
                continue

            # The unique ID string is used as the column header
            col_name = str(neighbor_id)

            # Generate predictions for the specific neighbor
            query = RecQuery(user_id=neighbor_id)
            scores_itemlist = score(self.pipeline, query, list(self.items))

            neighbor_scores_df = scores_itemlist.to_df()
            neighbor_scores_df = neighbor_scores_df.rename(columns={'item_id': 'item', 'score': col_name})
            scores_df = pd.merge(scores_df, neighbor_scores_df[['item', col_name]], how='left', on='item')

        # Calculate Variance (Across Neighbors)
        # Drop the 'item' column to leave only the prediction score columns
        scores_only_df = scores_df.drop(columns=['item']).apply(pd.to_numeric, errors='coerce')
        scores_df['variance'] = np.nanvar(scores_only_df, axis=1)

        scores_df = pd.merge(scores_df, self.item_popularity, how='left', on='item')

        return scores_df
