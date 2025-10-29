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
from itertools import count, islice, product
from typing import Literal

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial import ConvexHull

from rssa_api.data.schemas.participant_response_schemas import MovieLensRatingSchema
from rssa_api.data.schemas.preferences_schemas import PrefVizItem

from .mf_base import RSSABase

log = logging.getLogger(__name__)


class PreferenceVisualization(RSSABase):
    """
    Service for generating recommendations for the preference visualization based on
    similar user predicted scores.
    """

    def __init__(self, model_folder: str):
        super().__init__(model_folder)

    def get_prediction(
        self,
        ratings: list[MovieLensRatingSchema],
        user_id: str,
    ) -> pd.DataFrame:
        preds_df = self.predict(user_id, ratings)
        preds_df = preds_df.rename(columns={'item_id': 'item', 'score': 'user_score'})

        return preds_df

    def get_baseline_prediction(
        self, ratings: list[MovieLensRatingSchema], user_id: str, num_rec: int
    ) -> list[PrefVizItem]:
        preds = self.get_prediction(ratings, user_id).sort_values(by='score', ascending=False)
        preds = preds.head(num_rec)
        # FIXME: This is a hack to get it working using the current data model
        recommended_items = []
        for _, row in preds.iterrows():
            recommended_items.append(
                PrefVizItem(
                    item_id=str(int(row['item'])),  # truncate the trailing .0
                    community_score=0,
                    user_score=row['score'],
                    community_label=-1,
                    user_label=-1,
                    cluster=-1,
                )
            )

        return recommended_items

    def get_candidates(
        self,
        user_id: str,
        ratings: list[MovieLensRatingSchema],
        ave_score_type: Literal['global', 'nn_observed', 'nn_predicted'],
        min_rating_count: int = 50,
    ) -> pd.DataFrame:
        preds_df = self.get_prediction(ratings, user_id)
        candidates = pd.merge(preds_df, self.item_popularity, how='left', on='item')
        baseline_df = pd.DataFrame()

        if ave_score_type == 'global':
            # Global Observed Average is pre-calculated in self.ave_item_score.
            # It's already named 'ave_score' in the loaded CSV, so we use it directly.
            baseline_df = self.ave_item_score.copy()

        if ave_score_type == 'nn_observed':
            # Average Neighborhood Observed Ratings
            user_features = self.get_user_feature_vector(ratings)
            search_space_k = 200
            all_neighbors_ids = self.find_nearest_neighbors_annoy(
                new_user_vector=user_features,
                num_neighbors=search_space_k,
            )
            target_item_ids = set(preds_df['item_id'].to_list())
            observed_ratings_list = []
            for item_id in target_item_ids:
                neighborhood_avg = self.calculate_neighborhood_average(all_neighbors_ids, item_id, min_rating_count)
                observed_ratings_list.append({'item': item_id, 'ave_score': neighborhood_avg})
            average_neighbor_ratings = pd.DataFrame(observed_ratings_list)
            average_neighbor_ratings = average_neighbor_ratings.rename(columns={'rating': 'ave_score'})
            baseline_df = average_neighbor_ratings

        if ave_score_type == 'nn_predicted':
            # Average Neighborhood Predicted Ratings
            user_features = self.get_user_feature_vector(ratings)
            search_space_k = 200

            annoy_index, _ = self._load_annoy_assets_asset()
            nn_ids: list[int] = annoy_index.get_nns_by_vector(user_features, search_space_k, include_distances=False)
            del annoy_index
            del _
            neighbor_internal_codes_np: np.ndarray = np.array(nn_ids, dtype=np.int32)
            target_item_ids = set(preds_df['item_id'].to_list())
            p_nn_ave_df = self.calculate_predicted_neighborhood_average(
                neighbor_internal_codes_np, preds_df['item_id'].to_list()
            )
            baseline_df = p_nn_ave_df.rename(columns={'p_nn_ave_score': 'ave_score'})
        if not baseline_df.empty:
            candidates = pd.merge(
                candidates,
                baseline_df[['item', 'ave_score']],
                how='left',
                on='item',
                suffixes=('_user', '_baseline'),
            )

        candidates = candidates[candidates['count'] >= min_rating_count].copy()
        candidates.dropna(inplace=True)
        candidates.index = pd.Index(candidates['item'].values)

        return candidates

    def calculate_predicted_neighborhood_average(
        self, neighbor_internal_codes: np.ndarray, target_item_ids: list[int]
    ) -> pd.DataFrame:
        user_features = self.model.user_features_
        if user_features is None:
            return pd.DataFrame()

        Q_target_slice, valid_item_ids = self.get_target_item_factors(target_item_ids)
        P_neighbors_slice = user_features[neighbor_internal_codes, :]

        Pred_Matrix = P_neighbors_slice @ Q_target_slice.T

        P_NN_Ave_Vector = np.mean(Pred_Matrix, axis=0)
        p_nn_ave_df = pd.DataFrame({'p_nn_ave_score': P_NN_Ave_Vector}, index=valid_item_ids)
        p_nn_ave_df.index_name = 'item'
        return p_nn_ave_df.reset_index()

    def predict_diverse_items(
        self,
        ratings: list[MovieLensRatingSchema],
        num_rec: int,
        user_id: str,
        algo: str = 'fishnet',
        init_sample_size: int = 500,
        min_rating_count: int = 50,
    ) -> list[PrefVizItem]:
        ratedset = tuple([r.item_id for r in ratings])
        seed = hash(ratedset) % (2**32)
        np.random.seed(seed)  # Set the NumPy seed for repeatable sampling/shuffling

        candidates = self.get_candidates(user_id, ratings, 'global')
        diverse_items: pd.DataFrame = candidates.copy()

        if algo == 'fishnet':
            # Assumes the corrected _fishingnet returns the final DataFrame of size num_rec
            diverse_items = self._fishingnet(candidates, num_rec)

        elif algo == 'single_linkage':
            # Stratified sampling before clustering to ensure coverage of score range

            candidates.sort_values(by='score', ascending=False, inplace=True)
            candlen = len(candidates)

            # Ensure sampling doesn't exceed available data
            sample_size = min(init_sample_size, int(candlen / 3))

            # Calculate indices for Top, Middle, Bottom samples
            mid_start = int(candlen / 2) - int(sample_size / 2)

            topn_user = candidates.head(sample_size).copy()
            botn_user = candidates.tail(sample_size).copy()
            midn_user = candidates.iloc[mid_start : mid_start + sample_size].copy()

            sampled_candidates = pd.concat([topn_user, botn_user, midn_user]).drop_duplicates()

            # Cluster the sampled data into num_rec clusters
            diverse_items = self._single_linkage_clustering(sampled_candidates, num_rec)

        elif algo == 'random':
            # Simple random sampling (always reproducible due to np.random.seed(seed))
            n_sample = min(num_rec, len(candidates))
            diverse_items = candidates.sample(n=n_sample)

        elif algo == 'fishnet + single_linkage':
            # Two-stage process: Filter by grid coverage, then cluster the results

            initial_candidates = self._fishingnet(candidates, init_sample_size)
            diverse_items = self._single_linkage_clustering(initial_candidates, num_rec)
        elif algo == 'convexhull':
            diverse_items = self._convexhull(candidates)
            # TODO: we should pick num_rec items
        else:
            # Default fallback (e.g., just top predicted items)
            n_default = min(num_rec, len(candidates))
            diverse_items = candidates.sort_values(by='score', ascending=False).head(n_default)

        scaled_items, _, _ = self.scale_and_label(diverse_items)

        recommended_items = []
        for _, row in scaled_items.iterrows():
            recommended_items.append(
                PrefVizItem(
                    item_id=str(int(row['item'])),  # truncate the trailing .0
                    community_score=row['community'],
                    user_score=row['user'],
                    community_label=row['community_label'],
                    user_label=row['user_label'],
                    cluster=int(row['cluster']) if 'cluster' in row else 0,
                )
            )

        return recommended_items

    def predict_reference_items(
        self,
        ratings: list[MovieLensRatingSchema],
        num_rec: int,
        user_id: str,
        init_sample_size: int = 500,
        min_rating_count: int = 50,
    ) -> list[PrefVizItem]:
        candidates = self.get_candidates(user_id, ratings, ave_score_type='nn_predicted')

        diverse_items, _ = self.__fishingnet(candidates, init_sample_size)
        diverse_items = self.__single_linkage_clustering(diverse_items, num_rec)

        scaled_items, scaled_avg_comm, scaled_avg_user = self.scale_and_label(diverse_items)

        recommended_items = []
        for _, row in scaled_items.iterrows():
            recommended_items.append(
                PrefVizItem(
                    item_id=str(int(row['item'])),  # truncate the trailing .0
                    community_score=row['community'],
                    user_score=row['user'],
                    community_label=row['community_label'],
                    user_label=row['user_label'],
                    cluster=int(row['cluster']) if 'cluster' in row else 0,
                )
            )

        return recommended_items

    def seeding(self, n, nb):
        return list(islice(count(n, (n - 1) / nb), nb + 1))

    def scale_grid(self, minval, maxval, num_divisions):
        ticks = [minval]
        step = (maxval - minval) / num_divisions
        for i in range(num_divisions):
            ticks.append(ticks[i] + step)

        grid = list(product(ticks, ticks))
        grid = np.asarray(grid, dtype=np.float64)

        return grid

    def _convexhull(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """
        Identifies the set of items that define the outer boundary (Convex Hull)
        in the 2D score space (user_score vs. ave_score).

        These items represent the extremes of the model's predictions for the user.

        Args:
            candidates (pd.DataFrame): DataFrame containing item candidates, must
                                    include 'user_score' and 'ave_score'.

        Returns:
            pd.DataFrame: A DataFrame containing only the items that lie on the
                        convex hull boundary.
        """
        if candidates.shape[0] < 3:
            # A Convex Hull requires at least 3 points
            return candidates

        # Use the 2D score space: (User Score, Community Score)
        X = candidates[['user_score', 'ave_score']].values

        # This finds the indices of the points (rows in X) that form the convex hull.
        try:
            hull = ConvexHull(X)
        except Exception as e:
            # Handle the edge case where points are perfectly collinear (rare, but possible)
            log.warning(f'ConvexHull computation failed (collinearity): {e}')
            return candidates.head()  # Return a small set of candidates as a fallback

        # hull.vertices contains the indices of the points that form the hull's boundary.
        hull_indices = hull.vertices

        # Use the indices to select the corresponding rows from the candidates DataFrame
        extreme_items = candidates.iloc[hull_indices].copy()

        log.info(f'Convex Hull analysis found {len(extreme_items)} extreme items.')

        return extreme_items

    def _fishingnet(self, candidates: pd.DataFrame, n: int = 80) -> pd.DataFrame:
        """
        Performs grid-based sampling to select N items that are maximally diverse
        in the 2D score space, ensuring the selected items cover the grid widely.

        Args:
            candidates (pd.DataFrame): Input candidates, indexed by item ID.
            n (int): The target number of items to select (should match the number of grid points used).

        Returns:
            pd.DataFrame: A DataFrame containing the N selected diverse items.
        """
        if candidates.empty:
            return candidates

        # Extract the (score, ave_score) feature space
        X = candidates[['user_score', 'ave_score']].values

        # Assume scale_grid returns a list of N coordinates: [(x1, y1), (x2, y2), ...]
        grid_points = self.scale_grid(minval=1, maxval=5, num_divisions=int(np.sqrt(n)))

        # Use a boolean mask to track which candidates have already been selected
        is_selected = np.zeros(len(candidates), dtype=bool)

        selected_items_list = []

        # Greedy Search Loop (Iterate over the N grid points)
        for point in grid_points:
            # Calculate Manhattan distance from *every unselected candidate* to the grid point
            # np.abs(X - point) gives the 2D distance for every item to the point
            dist_to_point = np.sum(np.abs(X - point), axis=1)

            # Apply the selection mask to restrict search to unselected items
            current_distances = dist_to_point.copy()
            current_distances[is_selected] = np.inf  # Ignore already selected items

            # Find the index of the closest UNSELECTED item
            if np.all(is_selected):
                break  # Stop if all items have been selected

            idx_closest_candidate = np.argmin(current_distances)

            selected_items_list.append(candidates.iloc[idx_closest_candidate])
            is_selected[idx_closest_candidate] = True
            if len(selected_items_list) >= n:
                break

        return pd.DataFrame(selected_items_list)

    def _single_linkage_clustering(self, candidates: pd.DataFrame, num_clusters: int = 80) -> pd.DataFrame:
        """
        Performs Single Linkage Clustering (equivalent to your MST cut) on the
        2D score space (user_score, ave_score) and assigns cluster IDs.

        Args:
            candidates (pd.DataFrame): DataFrame containing item candidates.
            num_clusters (int): The target number of clusters (N) to form.

        Returns:
            pd.DataFrame: Candidates DataFrame with the 'cluster' ID assigned.
        """
        if candidates.shape[0] == 0:
            return candidates

        X = candidates[['user_score', 'ave_score']].values

        # Uses fast C/Fortran code to calculate distances and build the linkage matrix.
        linkage_matrix = linkage(X, method='single', metric='cityblock')

        # To form N clusters, we cut the dendrogram at a distance such that N clusters remain.
        # fcluster cuts the tree and assigns cluster labels (1 to N).

        # NOTE: The cluster numbering depends on the structure of the tree.
        cluster_labels = fcluster(linkage_matrix, t=num_clusters, criterion='maxclust')

        candidates['cluster'] = cluster_labels

        # Select one item per cluster.
        final_items = []

        for i in range(1, num_clusters + 1):
            cluster_df = candidates[candidates['cluster'] == i].copy()

            if not cluster_df.empty:
                # Find the center/centroid of the cluster for selection
                mid_score = cluster_df['user_score'].mean()
                mid_ave = cluster_df['ave_score'].mean()

                # Calculate Manhattan distance from the mean center to find the closest item
                cluster_df['dist_to_center'] = np.abs(cluster_df['user_score'] - mid_score) + np.abs(
                    cluster_df['ave_score'] - mid_ave
                )

                # Select the item closest to the cluster center as the representative
                representative_item = cluster_df.sort_values(by='dist_to_center', ascending=True).iloc[0]

                final_items.append(representative_item)

        return pd.DataFrame(final_items)

    def scale_and_label(self, items, new_min=1, new_max=5):
        scaled_items = items.copy()
        scaled_items.rename(columns={'ave_score': 'community', 'user_score': 'user'}, inplace=True)
        # Label the items based on the global average
        global_avg = np.mean([np.median(scaled_items['community']), np.median(scaled_items['user'])])

        def label(row):
            row['community_label'] = 1 if row['community'] >= global_avg else 0
            row['user_label'] = 1 if row['user'] >= global_avg else 0
            return row

        labeled_items = scaled_items.apply(label, axis=1)
        labeled_items = labeled_items.astype(
            {'item': 'int64', 'count': 'int64', 'community_label': 'int64', 'user_label': 'int64'}
        )
        avg_comm_score = np.mean(labeled_items['community'])
        avg_user_score = np.mean(labeled_items['user'])

        return labeled_items, avg_comm_score, avg_user_score
