"""
----
File: common.py
Project: RS:SA Recommender System (Clemson University)
Created Date: Friday, 1st September 2023
Author: Mehtab 'Shahan' Iqbal
Affiliation: Clemson University
----
Last Modified: Friday, 10th October 2025 2:56:58 am
Modified By: Mehtab 'Shahan' Iqbal (mehtabi@clemson.edu)
----
Copyright (c) 2025 Clemson University
License: MIT License (See LICENSE.md)
# SPDX-License-Identifier: MIT License
"""

from typing import cast

import binpickle
import numpy as np
import pandas as pd
from annoy import AnnoyIndex
from lenskit import score
from lenskit.als import ALSBase
from lenskit.data import ItemList, RecQuery
from lenskit.pipeline import Pipeline
from lenskit.pipeline.nodes import ComponentInstanceNode
from scipy.spatial.distance import cosine

from data.schemas.participant_response_schemas import MovieLensRatingSchema


def rssa_predict(pipeline: Pipeline, all_items_df: pd.DataFrame, user_id: str, ratings: pd.Series) -> pd.DataFrame:
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

    candidate_items = all_items_df['item'].to_list()
    user_ratings = ItemList(ratings, field_name='rating')
    query = RecQuery(user_id=user_id, user_items=user_ratings)

    als_preds_il = score(pipeline, query, candidate_items)
    als_preds = als_preds_il.to_df()
    als_preds = als_preds[['item_id', 'score']].rename(columns={'item_id': 'item'})

    print('als_preds: ', als_preds)
    return als_preds


def predict_discounted(
    pipeline: Pipeline, items: pd.DataFrame, userid: str, ratings: pd.Series, factor: int, coeff: float = 0.5
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
    als_preds = rssa_predict(pipeline, items, userid, ratings)

    als_preds = pd.merge(als_preds, items, how='left', on='item')
    als_preds['discounted_score'] = als_preds['score'] - coeff * (als_preds['count'] / factor)

    als_preds.sort_values(by='discounted_score', ascending=False, inplace=True)

    return als_preds


def get_user_feature_vector(pipeline: Pipeline, ratings: list[MovieLensRatingSchema]) -> np.ndarray:
    """
    Extracts the new user's latent feature vector (q_u)
    using the Scorer's public new_user_embedding method.

    Args:
        pipeline (Pipeline): The trained pipeline object.
        ratings (pd.Series): The new user's ratings history (indexed by item ID).

    Returns:
        np.ndarray: The projected user feature vector (q_u).
    """

    data = [{'item_id': r.item_id, 'rating': float(r.rating)} for r in ratings]
    ratings_df = pd.DataFrame(data)
    pipeline_component: ComponentInstanceNode = cast(ComponentInstanceNode, pipeline.node('scorer'))
    scorer: ALSBase = cast(ALSBase, pipeline_component.component)
    item_vocab = scorer.items_
    item_numbers_array = item_vocab.numbers(ratings_df['item_id'].to_numpy(), missing='error')

    ratings_df['item_num'] = item_numbers_array

    user_history_itemlist = ItemList.from_df(
        ratings_df,
    )
    user_vector_tuple = scorer.new_user_embedding(None, user_history_itemlist)
    user_tensor = user_vector_tuple[0]
    user_vector_numpy = user_tensor.cpu().detach().numpy()

    return user_vector_numpy.flatten()


class RSSABase:
    def __init__(self, model_path: str, item_popularity, ave_item_score):
        self.item_popularity = item_popularity
        self.ave_item_score = ave_item_score
        self.items = item_popularity.item.unique()

        self.model_path = model_path
        self.pipeline: Pipeline = self._import_trained_model()

        self.scorer: ALSBase = self._get_trained_scorer()

        self.annoy_index, self.user_map_lookup = self._load_annoy_assets()

    def _import_trained_model(self):
        return binpickle.load(f'{self.model_path}model.bpk')

    def _get_trained_scorer(self) -> ALSBase:
        """
        Extracts the trained Scorer instance (ALSBase) from the loaded Pipeline.
        Uses the confirmed pattern: pipeline.run(node) on the component node.
        """
        pipeline_component: ComponentInstanceNode = cast(ComponentInstanceNode, self.pipeline.node('scorer'))
        scorer: ALSBase = cast(ALSBase, pipeline_component.component)

        return scorer

    def _load_annoy_assets(self):
        """Loads the pre-built Annoy index and the ID mapping table."""

        annoy_index_path = f'{self.model_path}annoy_index'
        user_map_path = f'{annoy_index_path}_map.csv'

        # Note: Scorer must be loaded before calling this method
        user_feature_vector = self.scorer.user_features_
        if user_feature_vector is None:
            raise RuntimeError()

        dims = user_feature_vector.shape[1]

        # Load Annoy Index
        index = AnnoyIndex(dims, 'angular')
        try:
            index.load(annoy_index_path)
        except Exception as e:
            raise FileNotFoundError(
                f'Annoy index file not found at {annoy_index_path}. Did you run training with --cluster_index?'
            ) from e

        # Load User Map (Annoy ID -> UUID)
        user_map_df = pd.read_csv(user_map_path, index_col=0)

        # Convert the Series/DataFrame to a fast dictionary lookup (internal ID -> external ID)
        # Assuming the CSV saved was index=Internal ID, column=External UUID
        return index, user_map_df.iloc[:, 0].to_dict()  # Use iloc[0] to grab the first column (the UUIDs)

    def _similarity_user_features(self, umat, users, feature_newUser, method='cosine'):
        """
        ALS has already pre-weighted the user features/item features;
        Use either the Cosine distance(by default) or the Eculidean distance;
        umat: np.ndarray
        users: Int64Index
        feature_newUser: np.ndarray
        """
        nrows, ncols = umat.shape
        distance = []
        if method == 'cosine':
            distance = [cosine(umat[i,], feature_newUser) for i in range(nrows)]
        elif method == 'euclidean':
            distance = [np.linalg.norm(umat[i,] - feature_newUser) for i in range(nrows)]

        distance = pd.DataFrame({'user': users.values, 'distance': distance})

        return distance

    def _find_neighbors(self, umat, users, feature_newUser, distance_method, num_neighbors):
        similarity = self._similarity_user_features(umat, users, feature_newUser, distance_method)
        neighbors_similarity = similarity.sort_values(by='distance', ascending=True).head(num_neighbors)

        return neighbors_similarity

    def _find_nearest_neighbors_annoy(self, new_user_vector: np.ndarray, num_neighbors: int) -> list[str]:
        """
        Finds K nearest neighbors using the pre-built Annoy index over the P matrix.

        Args:
            new_user_vector (np.ndarray): The projected 1D vector (q_u) of the new user.
            num_neighbors (int): The number of neighbors (K) to retrieve.

        Returns:
            list[str]: A list of external UUIDs (string format) of the K neighbors.
        """
        internal_ids: list[int] = self.annoy_index.get_nns_by_vector(
            new_user_vector, num_neighbors, include_distances=False
        )

        external_ids: list[str] = [self.user_map_lookup[i] for i in internal_ids]

        return external_ids


def scale_value(value, new_min, new_max, cur_min, cur_max):
    new_range = new_max - new_min
    cur_range = cur_max - cur_min
    new_value = new_range * (value - cur_min) / cur_range + new_min
    return new_value
