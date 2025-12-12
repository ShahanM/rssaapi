"""
----
File: alt_rec_service.py
Project: RS:SA Recommender System (Clemson University)
Created Date: Monday, 13th October 2025
Author: Mehtab 'Shahan' Iqbal and Lijie Guo
Affiliation: Clemson University
----
Last Modified: Sunday, 2nd November 2025 10:17:59 pm
Modified By: Mehtab 'Shahan' Iqbal (mehtabi@clemson.edu)
----
Copyright (c) 2025 Clemson University
License: MIT License (See LICENSE.md)
# SPDX-License-Identifier: MIT License
"""

from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
from scipy.spatial import distance
from sklearn.preprocessing import MinMaxScaler

from rssa_api.data.schemas.preferences_schemas import (
    EmotionContinuousInputSchema,
    EmotionDiscreteInputSchema,
)
from rssa_api.services.recommendation.mf_base import RSSABase
from rssa_api.data.schemas.participant_response_schemas import MovieLensRating


class EmotionsRS(RSSABase):
    """
    Extends RSSABase to provide emotion-aware recommendations.

    This class adds functionality to tune standard matrix factorization
    recommendations based on user-specified emotional preferences,
    and to diversify recommendation lists based on item emotion features.
    """

    norm = 'L1'

    def __init__(self, model_folder: str):
        """
        Initializes the EmotionsRS service.

        Args:
            model_folder: The directory containing the trained model assets.
        """
        super().__init__(model_folder)

        self.emotion_tags = ['anger', 'anticipation', 'disgust', 'fear', 'joy', 'sadness', 'surprise', 'trust']
        self.discounting_factor = self._init_discounting_factor(self.item_popularity)
        self.discounting_coefficient = 0.5  # FIXME: Should be loaded from a configuration source

    def _init_discounting_factor(self, item_popularity):
        """
        Calculates the exponent factor used to scale down popularity counts.

        Args:
            item_popularity: DataFrame with ['item', 'count', 'rank_popular'].

        Returns:
            The scaling factor (power of 10).
        """
        max_count = item_popularity['count'].max()
        return 10 ** len(str(max_count))

    def _load_emotion_lookup_asset(self) -> pd.DataFrame:
        """
        Loads the item-emotion feature lookup table from parquet.

        Returns:
            A DataFrame indexed by 'item' with emotion tags as columns.
        """
        emotions_path = f'{self.path}/item_emotion_lookup.parquet'
        emotions_df = pd.read_parquet(emotions_path)
        return emotions_df

    def set_norm(self, norm: str) -> None:
        """
        Sets the distance norm to use (L1 or L2).

        Args:
            norm: The norm to use, 'L1' (cityblock) or 'L2' (euclidean).

        Raises:
            ValueError: If norm is not 'L1' or 'L2'.
        """
        if norm.lower() not in ['l1', 'l2']:
            raise ValueError('The value of norm must be either L1, or L2.')

        self.norm = norm.upper()

    def _compute_distance(self, u: ArrayLike, v: ArrayLike) -> Any:
        """
        Computes a single distance between two vectors based on self.norm.

        Args:
            u: First vector.
            v: Second vector.

        Returns:
            The distance (float).
        """
        if self.norm == 'L1':
            return distance.cityblock(u, v)

        if self.norm == 'L2':
            return distance.euclidean(u, v)

    def predict_topN(self, user_id: str, ratings: list[MovieLensRating], n: int) -> list[int]:
        """
        Predicts the top N items for a user, filtering out already-rated items.

        Args:
            user_id: The user's ID.
            ratings: A list of the user's rated items.
            n: The number of recommendations to return.

        Returns:
            A list of N recommended item IDs.
        """
        rated_items = {r.item_id for r in ratings}
        _preds = self.predict_discounted(user_id, ratings, self.discounting_factor)
        top_n_preds = _preds[~_preds['item'].isin(rated_items)].head(n)

        return top_n_preds['item'].astype(int).to_list()

    def predict_diverseN(
        self,
        user_id: str,
        ratings: list[MovieLensRating],
        num_rec: int,
        item_pool_size: int,
        sampling_size: int,
    ) -> list[int]:
        """
        Predict diverse N items using the Diverse Top-N recommendation by
        diversifying the RSSA discounted predictions.

        Args:
            ratings: List of rated items.
            user_id: User ID.
            num_rec: Number of recommendations to make.
            dist_method: Distance method (Note: currently unused, self.norm is used).
            weight_sigma: Weight sigma.
            item_pool_size: Item pool size to seed diverseN.
            sampling_size: Number of items to sample from the candidate item pool.

        Returns:
            A list of diverse N item IDs.
        """
        diverseN = self._predict_diverseN_by_emotion(ratings, user_id, item_pool_size, sampling_size)

        return list(map(int, diverseN.head(num_rec)['item']))

    def _get_candidate_item(
        self,
        ratings: list[MovieLensRating],
        user_id: str,
        item_pool_size: int,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Gets the initial pool of candidate items and their emotion features.

        Args:
            ratings: List of rated items.
            user_id: User ID.
            item_pool_size: Item pool size to generate initial candidate items.

        Returns:
            A tuple of:
                - candidate_items (pd.DataFrame): Candidate items and scores.
                - candidate_item_emotions (pd.DataFrame): Emotion features for
                the candidate items, indexed by 'item'.
        """
        preds = self.predict_discounted(user_id, ratings, self.discounting_factor)
        candidates = preds.head(item_pool_size)
        candidate_ids = candidates.item.unique()

        emotions_lookup = self._load_emotion_lookup_asset()
        candidate_items_emotions = emotions_lookup.loc[candidate_ids]

        return candidates, candidate_items_emotions

    def _predict_tuned_topN(
        self,
        ratings: list[MovieLensRating],
        user_id: str,
        user_emotion_tags: list[str],
        user_emotion_vals: list[float],
        sort_order: bool,
        scale_vector: bool,
        ranking_strategy: str,
        item_pool_size: int,
    ) -> pd.DataFrame:
        """
        Predict top N items tuned by user emotion input.

        Args:
            ratings: List of rated items.
            user_id: User ID.
            user_emotion_tags: List of user emotion tags.
            user_emotion_vals: List of user emotion values.
            sort_order: Sort order for distance ranking.
            scale_vector: Whether to scale the vector.
            ranking_strategy: 'distance' or 'weighted'.
            dist_method: Distance method (Note: currently unused, self.norm is used).
            item_pool_size: Item pool size to generate initial candidate items.

        Returns:
            A DataFrame of tuned recommendations, sorted appropriately.
        """

        candidate_items, candidate_item_emotions = self._get_candidate_item(ratings, user_id, item_pool_size)

        # Ensure candidate_item_emotions is a DataFrame with 'item' as a column
        # if it's not already (e.g., if it was indexed)
        if 'item' not in candidate_item_emotions.columns:
            candidate_item_emotions = candidate_item_emotions.reset_index()

        if ranking_strategy == 'distance':
            return self._get_distance_to_input(
                candidate_item_emotions, user_emotion_tags, user_emotion_vals, sort_order, scale_vector
            )

        if ranking_strategy == 'weighted':
            new_ranking_score_df = self._weighted_ranking(
                candidate_items[['item', 'discounted_score']],
                user_emotion_tags,
                user_emotion_vals,
                candidate_item_emotions,
            )
            new_ranking_score_df_sorted = new_ranking_score_df.sort_values(by='new_rank_score', ascending=False)
            return new_ranking_score_df_sorted

        raise NotImplementedError

    def _get_distance_to_input(
        self,
        emotions_items: pd.DataFrame,
        user_emotion_tags: list[str],
        user_emotion_vals: list[float],
        sort_order: bool,
        scale_vector: bool,
    ) -> pd.DataFrame:
        """
        Calculates distance from each item to the user's emotion vector.

        Args:
            emotions_items: DataFrame of items and their emotion features.
            user_emotion_tags: List of emotion tags to use for distance.
            user_emotion_vals: List of target emotion values.
            sort_order: Whether to sort ascending (True) or descending (False).
            scale_vector: Whether to scale the target vector.

        Returns:
            DataFrame ['item', 'distance'] sorted by distance.
        """
        emotion_item_ids = emotions_items['item'].to_numpy()
        emotions_items_ndarray = emotions_items[user_emotion_tags].to_numpy()

        distance_to_input = self._emotion_distance(emotions_items_ndarray, np.array(user_emotion_vals), scale_vector)

        distance_to_input_df = pd.DataFrame(
            {'item': emotion_item_ids, 'distance': distance_to_input}, columns=['item', 'distance']
        )
        distance_to_input_df_sorted = distance_to_input_df.sort_values(by='distance', ascending=sort_order)

        return distance_to_input_df_sorted

    def _process_discrete_emotion_input(
        self, emotion_input: list[EmotionDiscreteInputSchema], lowval: float, highval: float
    ) -> tuple[list[str], list[str], list[float]]:
        """
        Process discrete emotion input into specified and unspecified lists.

        Args:
            emotion_input: List of discrete emotion input schemas.
            lowval: The float value corresponding to 'low'.
            highval: The float value corresponding to 'high'.

        Returns:
            A tuple of:
                - specified_emotion_tags (list[str])
                - unspecified_emotion_tags (list[str])
                - specified_emotion_vals (list[float])
        """
        specified_emotion_tags = []
        specified_emotion_vals = []
        unspecified_emotion_tags = []

        # Use a dict for O(1) lookups
        emo_dict = {emo.emotion.lower(): emo.weight for emo in emotion_input}

        for emo in self.emotion_tags:
            weight = emo_dict.get(emo)  # Use .get for safety
            if weight == 'low':
                specified_emotion_tags.append(emo)
                specified_emotion_vals.append(lowval)
            elif weight == 'high':
                specified_emotion_tags.append(emo)
                specified_emotion_vals.append(highval)
            else:
                unspecified_emotion_tags.append(emo)

        return specified_emotion_tags, unspecified_emotion_tags, specified_emotion_vals

    def predict_discrete_tuned_topN(
        self,
        user_id: str,
        ratings: list[MovieLensRating],
        emotion_input: list[EmotionDiscreteInputSchema],
        num_rec: int,
        scale_vector: bool,
        lowval: float,
        highval: float,
        ranking_strategy: str,
        dist_method: str,
        item_pool_size: int,
    ) -> list[int]:
        """
        Predicts Top-N items tuned by discrete (low/med/high) emotion inputs.

        Args:
            ratings: List of rated items.
            user_id: User ID.
            emotion_input: List of discrete emotion inputs.
            num_rec: Number of recommendations.
            scale_vector: Whether to scale the vector.
            lowval: Float value for 'low'.
            highval: Float value for 'high'.
            ranking_strategy: 'distance' or 'weighted'.
            dist_method: Distance method (Note: currently unused).
            item_pool_size: Item pool size.

        Returns:
            A list of tuned Top-N item IDs.
        """
        user_specified_emotion_tags, _, user_specified_emotion_vals = self._process_discrete_emotion_input(
            emotion_input, lowval, highval
        )

        tuned_topN = self._predict_tuned_topN(
            ratings,
            user_id,
            user_specified_emotion_tags,
            user_specified_emotion_vals,
            True,  # sort_order=True (ascending distance)
            scale_vector,
            ranking_strategy,
            item_pool_size,
        )

        return list(map(int, tuned_topN.head(num_rec)['item']))

    def predict_continuous_tuned_topN(
        self,
        ratings: list[MovieLensRating],
        user_id,
        emotion_input: list[EmotionContinuousInputSchema],
        num_rec: int,
        scale_vector: bool,
        algo: str,
        dist_method: str,
        item_pool_size,
    ) -> list[int]:
        """
        Predicts Top-N items tuned by continuous (float) emotion inputs.

        Args:
            ratings: List of rated items.
            user_id: User ID.
            emotion_input: List of continuous emotion inputs.
            num_rec: Number of recommendations.
            scale_vector: Whether to scale the vector.
            algo: Ranking strategy ('distance' or 'weighted').
            dist_method: Distance method (Note: currently unused).
            item_pool_size: Item pool size.

        Returns:
            A list of tuned Top-N item IDs.
        """
        user_emotion_tags = [one_emotion.emotion for one_emotion in emotion_input]
        user_emotion_vals = [one_emotion.weight for one_emotion in emotion_input]

        user_emotion_dict = dict(zip(user_emotion_tags, user_emotion_vals))

        user_specified_emotion_tags = []
        user_unspecified_emotion_tags = []
        user_specified_emotion_vals = []

        # Separate tags with non-zero weights
        for k, v in user_emotion_dict.items():
            if v != 0:
                user_specified_emotion_tags.append(k)
                user_specified_emotion_vals.append(v)
            else:
                user_unspecified_emotion_tags.append(k)

        tuned_topN = self._predict_tuned_topN(
            ratings,
            user_id,
            user_specified_emotion_tags,
            user_specified_emotion_vals,
            False,  # sort_order=False (descending score)
            scale_vector,
            algo,  # ranking_strategy
            item_pool_size,
        )

        return list(map(int, tuned_topN.head(num_rec)['item']))

    def _predict_tuned_diverseN(
        self,
        ratings: list[MovieLensRating],
        user_id,
        user_emotion_tags: list[str],
        user_emotion_vals: list[float],
        unspecified_emotion_tags: list[str],
        sort_order: bool,
        scale_vector: bool,
        ranking_strategy: str,
        div_crit: str,
        item_pool_size: int,
        sampling_size: int,
    ) -> pd.DataFrame:
        """
        Predicts diversified N items, tuned by user emotion input.

        First diversifies, then re-ranks the diversified set based on
        emotion input.

        Args:
            ratings: List of rated items.
            user_id: User ID.
            user_emotion_tags: List of specified emotion tags.
            user_emotion_vals: List of specified emotion values.
            unspecified_emotion_tags: List of unspecified emotion tags.
            sort_order: Sort order for distance ranking.
            scale_vector: Whether to scale the vector.
            ranking_strategy: 'distance' or 'weighted'.
            dist_method: Distance method (Note: currently unused).
            div_crit: 'all' or 'unspecified' (which tags to use for diversity).
            item_pool_size: Item pool size.
            sampling_size: Number of items to sample for diversification.

        Returns:
            A DataFrame of tuned, diversified recommendations.
        """
        candidate_items, candidate_item_emotions = self._get_candidate_item(ratings, user_id, item_pool_size)

        query_tags = self.emotion_tags
        if div_crit == 'unspecified':
            query_tags = unspecified_emotion_tags

        candidate_ndarry = candidate_item_emotions[query_tags].to_numpy()

        [rec_items, item_emotions] = self._diversify_item_feature(
            candidate_items,
            candidate_ndarry,
            candidate_item_emotions.index.to_numpy(),
            sampling_size,
        )

        # Re-fetch emotions for the diversified set, indexed by item
        candidate_ids = rec_items['item'].unique()
        emotions_lookup = self._load_emotion_lookup_asset()
        candidates_for_similarity_emotions = emotions_lookup.loc[candidate_ids].reset_index()

        if ranking_strategy == 'distance':
            return self._get_distance_to_input(
                candidates_for_similarity_emotions,
                user_emotion_tags,
                user_emotion_vals,
                sort_order,
                scale_vector,
            )

        if ranking_strategy == 'weighted':
            return self._weighted_ranking(
                rec_items[['item', 'discounted_score']],
                user_emotion_tags,
                user_emotion_vals,
                candidates_for_similarity_emotions,
            )

        raise NotImplementedError

    def _weighted_ranking(
        self,
        original_rec_df: pd.DataFrame,
        user_emotion_tags: list[str],
        user_emotion_vals: list[float],
        candidate_item_emotions_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Re-ranks a set of recommendations using a weighted score.

        The new score combines the original recommendation rank (scaled)
        and a weighted sum of the item's emotion features.

        Args:
            original_rec_df: DataFrame with ['item', 'discounted_score'].
            user_emotion_tags: List of emotion tags to use.
            user_emotion_vals: List of weights for each emotion tag.
            candidate_item_emotions_df: DataFrame with item emotion features.

        Returns:
            A DataFrame with the new 'new_rank_score' column, sorted.
        """

        original_rec_df['ori_rank'] = np.arange(len(original_rec_df), 0, -1)

        recs_emotions_df = pd.merge(original_rec_df, candidate_item_emotions_df, on='item')
        col_query = ['ori_rank'] + user_emotion_tags
        candidate_df_to_scale = recs_emotions_df[col_query]

        scaler = MinMaxScaler()
        candidates_df_scaled = scaler.fit_transform(candidate_df_to_scale.to_numpy())
        candidates_df_scaled = pd.DataFrame(candidates_df_scaled, columns=col_query)

        # Convert user_emotion_vals to numpy array for broadcasting
        user_emotion_vals_np = np.array(user_emotion_vals)

        # Get scaled emotion values and scaled rank
        scaled_emotions = candidates_df_scaled[user_emotion_tags].values
        scaled_rank = candidates_df_scaled['ori_rank'].values

        # Calculate new score (vectorized)
        emotion_score = np.sum(scaled_emotions * user_emotion_vals_np, axis=1)
        rank_weight = 1 - np.sum(np.absolute(user_emotion_vals_np))
        rank_score = rank_weight * scaled_rank

        new_ranking_score = emotion_score + rank_score

        recs_emotions_df['new_rank_score'] = new_ranking_score
        recs_emotions_df.sort_values(by='new_rank_score', ascending=False, inplace=True)

        return recs_emotions_df

    def predict_discrete_tuned_diverseN(
        self,
        ratings: list[MovieLensRating],
        user_id: str,
        emotion_input: list[EmotionDiscreteInputSchema],
        num_rec: int,
        sampling_size: int,
        item_pool_size: int,
        scale_vector: bool,
        lowval: float,
        highval: float,
        ranking_strategy: str,
        div_crit: str,
    ) -> list[int]:
        """
        Predicts diversified N items, tuned by discrete emotion inputs.

        Args:
            ratings: List of rated items.
            user_id: User ID.
            emotion_input: List of discrete emotion inputs.
            num_rec: Number of recommendations.
            sampling_size: Number of items to sample.
            item_pool_size: Item pool size.
            scale_vector: Whether to scale the vector.
            lowval: Float value for 'low'.
            highval: Float value for 'high'.
            ranking_strategy: 'distance' or 'weighted'.
            dist_method: Distance method (Note: currently unused).
            div_crit: 'all' or 'unspecified'.

        Returns:
            A list of tuned, diversified Top-N item IDs.
        """
        user_specified_emotion_tags, user_unspecified_emotion_tags, user_specified_emotion_vals = (
            self._process_discrete_emotion_input(emotion_input, lowval, highval)
        )

        rec_diverseEmotion = self._predict_tuned_diverseN(
            ratings,
            user_id,
            user_specified_emotion_tags,
            user_specified_emotion_vals,
            user_unspecified_emotion_tags,
            True,  # sort_order=True (ascending distance)
            scale_vector,
            ranking_strategy,
            div_crit,
            item_pool_size,
            sampling_size,
        )

        return list(map(int, rec_diverseEmotion.head(num_rec)['item']))

    def _predict_diverseN_by_emotion(
        self,
        ratings: list[MovieLensRating],
        user_id: str,
        item_pool_size: int,
        sampling_size: int,
    ) -> pd.DataFrame:
        """
        Predicts Top-N diversified items based on emotion features.

        Args:
            ratings: List of rated items.
            user_id: User ID.
            dist_method: Distance method (Note: currently unused).
            weight_sigma: Weight sigma.
            item_pool_size: Item pool size.
            sampling_size: Number of items to sample.

        Returns:
            A DataFrame of diversified recommendations.
        """
        candidates, candidate_emotions = self._get_candidate_item(ratings, user_id, item_pool_size)
        item_ids = candidate_emotions.index.to_numpy()
        item_emotions_ndarray = candidate_emotions[self.emotion_tags].to_numpy()

        [rec_diverseEmotion, rec_itemEmotion] = self._diversify_item_feature(
            candidates, item_emotions_ndarray, item_ids, sampling_size
        )

        return rec_diverseEmotion

    def _diversify_item_feature(
        self,
        candidates: pd.DataFrame,
        vectors,
        items,
        sampling_size: int,
    ):
        """
        Diversify items using a greedy algorithm based on feature vectors.

        Args:
            candidates: DataFrame of candidate items and scores.
            vectors: NumPy array of feature vectors (N_items x N_features).
            items: NumPy array of item IDs corresponding to vectors.
            weighting: Weighting factor (unused).
            dist_method: Distance method (unused, self.norm is used).
            weight_sigma: Weighting factor (unused).
            sampling_size: Number of items to return.

        Returns:
            A tuple of:
                - recommendations (pd.DataFrame): Diversified items.
                - diverse_vectorsDf (pd.DataFrame): Features for diversified items.
        """
        # Set candidates index to 'item' for fast lookups
        if 'item' not in candidates.columns:
            candidates = candidates.reset_index()
        candidates = candidates.set_index('item')

        # Create DataFrame for vectors, indexed by item ID
        vectorsDf = pd.DataFrame(vectors, index=items)

        # Filter vectors to only those in the candidate set
        vectorsDf_in_candidate = vectorsDf[vectorsDf.index.isin(candidates.index)]

        # Reorder vectors to match the candidate order
        candidate_vectorsDf = vectorsDf_in_candidate.reindex(candidates.index)

        # Centroid and first candidate
        candidate_vectors = candidate_vectorsDf.to_numpy()
        items_candidate_vectors = candidate_vectorsDf.index.to_numpy()

        if candidate_vectors.shape[0] == 0:
            # No candidates, return empty
            return pd.DataFrame(columns=candidates.columns), pd.DataFrame(columns=vectorsDf.columns)

        centroid_vector = np.mean(candidate_vectors, axis=0)

        diverse_itemIDs = []
        diverse_vectors = np.empty([0, vectors.shape[1]])

        firstItem_index_val = self._first_item(centroid_vector, candidate_vectors, items_candidate_vectors)
        firstItem_vector = candidate_vectorsDf.loc[[firstItem_index_val]]

        diverse_vectors = np.concatenate((diverse_vectors, firstItem_vector.to_numpy()), axis=0)
        diverse_itemIDs.append(firstItem_index_val)

        candidate_vectorsDf_left = candidate_vectorsDf.drop(pd.Index([firstItem_index_val]))

        # Find the best next item one by one
        while len(diverse_itemIDs) < sampling_size and not candidate_vectorsDf_left.empty:
            nextItem_vector, nextItem_index = self._sum_distance(candidate_vectorsDf_left, diverse_vectors)

            candidate_vectorsDf_left = candidate_vectorsDf_left.drop(pd.Index([nextItem_index]))
            diverse_vectors = np.concatenate((diverse_vectors, nextItem_vector.to_numpy()), axis=0)
            diverse_itemIDs.append(nextItem_index)

        diverse_itemIDs = np.asarray(diverse_itemIDs)

        diverse_itemIDsDf = pd.DataFrame({'item': diverse_itemIDs}, index=diverse_itemIDs)

        diverse_vectorsDf = pd.DataFrame(diverse_vectors, index=diverse_itemIDs)

        # Reorder the original candidates to match the new diversified order
        recommendations = candidates.loc[diverse_itemIDsDf.index].reset_index()

        return recommendations, diverse_vectorsDf

    def _first_item(self, centroid, candidate_vectors, candidate_items):
        """
        Find the first item, (closest to the centroid).

        Args:
            centroid: Centroid vector.
            candidate_vectors: List of candidate item feature vectors.
            candidate_items: List of candidate item IDs.

        Returns:
            The item ID of the first item.
        """

        # Compute L1 (cityblock) distance from all candidates to the centroid
        # Use reshape to make centroid a 2D array (1 x N_features)
        dists = distance.cdist(candidate_vectors, centroid.reshape(1, -1), metric='cityblock').flatten()

        # Find the index of the item with the minimum distance
        first_index_pos = np.argmin(dists)

        # Return the corresponding item ID
        return candidate_items[first_index_pos]

    # def _sum_distance(self, candidate_vectorsDf: pd.DataFrame, diverse_set, method):
    #     """
    #     Find the next best item

    #     Parameters
    #     ----------
    #     candidate_vectorsDf : pd.DataFrame
    #             List of candidate item feature vectors
    #     diverse_set : np.ndarray
    #             List of diversified item feature vectors

    #     Returns
    #     -------
    #     bestItem_vector : pd.DataFrame
    #             Feature vector of the next best item
    #     bestItem_index : np.int64
    #             The index of the next best item
    #     """
    #     distance_cumulate = []
    #     candidate_vectors = candidate_vectorsDf.to_numpy()
    #     for row_candidate_vec in candidate_vectors:
    #         sum_dist = 0
    #         for row_diverse in diverse_set:
    #             dist = self._compute_distance(row_candidate_vec, row_diverse)
    #             sum_dist = sum_dist + dist
    #         distance_cumulate.append(sum_dist)
    #     distance_cumulate = pd.DataFrame({'sum_distance': distance_cumulate})
    #     distance_cumulate.index = candidate_vectorsDf.index
    #     distance_cumulate_sorted = distance_cumulate.sort_values(by='sum_distance', ascending=False)
    #     bestItem_index = distance_cumulate_sorted.index[0]
    #     bestItem_vector = candidate_vectorsDf[candidate_vectorsDf.index.isin(pd.Index([bestItem_index]))]

    #     return bestItem_vector, bestItem_index

    def _sum_distance(self, candidate_vectorsDf: pd.DataFrame, diverse_set: np.ndarray):
        """
        Find the next best item (farthest from the already selected set).

        Args:
            candidate_vectorsDf: DataFrame of remaining candidate vectors.
            diverse_set: NumPy array of vectors already in the diverse set.

        Returns:
            A tuple of:
                - bestItem_vector (pd.DataFrame): Feature vector of the next item.
                - bestItem_index (int): The item ID of the next best item.
        """

        candidate_vectors = candidate_vectorsDf.to_numpy()

        # Determine the metric based on the class 'norm'
        metric = 'cityblock' if self.norm == 'L1' else 'euclidean'

        # Compute distances from all candidates to all items in the diverse set
        # Shape: (n_candidates, n_diverse_set)
        dist_matrix = distance.cdist(candidate_vectors, diverse_set, metric=metric)

        # Sum distances for each candidate (axis=1)
        distance_cumulate = np.sum(dist_matrix, axis=1)

        # Find the index (position) of the candidate with the max sum-distance
        bestItem_pos = np.argmax(distance_cumulate)

        # Get the item ID (index label) from that position
        bestItem_index = candidate_vectorsDf.index[int(bestItem_pos)]

        # Get the vector using the position for iloc
        # Casting here too for consistency, although iloc is often more permissive
        bestItem_vector = candidate_vectorsDf.iloc[[int(bestItem_pos)]]

        return bestItem_vector, bestItem_index

    def _emotion_distance(
        self, matrix: np.ndarray, vector: np.ndarray, scale_vector: bool, norm: str = 'L1'
    ) -> np.ndarray:
        """
        Calculate the distance between a matrix of items and a target vector.

        Args:
            matrix: Emotion matrix (N_items x N_features).
            vector: Target emotion vector (N_features,).
            scale_vector: Whether to scale the target vector.

        Returns:
            A 1D NumPy array of distances.
        """
        if scale_vector:
            matrix_max = np.max(matrix, axis=0)
            matrix_min = np.min(matrix, axis=0)
            # Scale the target vector based on the matrix's range
            vector = (matrix_max - matrix_min) * vector

        # Determine the metric based on the class 'norm'
        metric = 'cityblock' if self.norm == 'L1' else 'euclidean'

        # Reshape vector to (1 x N_features) for cdist
        vector_2d = vector.reshape(1, -1)

        # Compute all distances at once and flatten to 1D array
        dist_array = distance.cdist(matrix, vector_2d, metric=metric).flatten()

        return dist_array
