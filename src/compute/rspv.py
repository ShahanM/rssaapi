"""
This file contains the RSSA Preference Visualization (RSPV) algorithms.

@Author: Mehtab Iqbal (Shahan)
@Affiliation: School of Computing, Clemson University
"""

import itertools
from typing import Callable, Tuple

import networkx as nx
import numpy as np
import pandas as pd
from lenskit.algorithms.als import _train_bias_row_lu

from data.schemas.participant_response_schemas import MovieLensRatingSchema, RatedItemBaseSchema
from data.schemas.preferences_schemas import PrefVizItem

from .common import RSSABase, get_user_feature_from_biasedMF, predict
from .utils import get_rating_data_path


class PreferenceVisualization(RSSABase):
    def __init__(self, model_path: str, item_popularity: pd.DataFrame, ave_item_score: pd.DataFrame):
        super().__init__(model_path, item_popularity, ave_item_score)

    def get_prediction(
        self,
        ratings: list[MovieLensRatingSchema],
        user_id: str,
    ) -> pd.DataFrame:
        rated_items = np.array([np.int64(rating.item_id) for rating in ratings])
        new_ratings = pd.Series(np.array([np.float64(rating.rating) for rating in ratings]), index=rated_items)

        als_preds = predict(self.model, self.item_popularity, user_id, new_ratings)

        return als_preds

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

    def predict_diverse_items(
        self,
        ratings: list[MovieLensRatingSchema],
        num_rec: int,
        user_id: str,
        algo: str = 'fishnet',
        randomize: bool = False,
        init_sample_size: int = 500,
        min_rating_count: int = 50,
    ) -> list[PrefVizItem]:
        # Get user predictions
        preds = self.get_prediction(ratings, user_id)

        # Merge predcitions with the average item score
        preds = pd.merge(preds, self.ave_item_score, how='left', on='item')

        # Merge the predictions with the item popularity
        preds = pd.merge(preds, self.item_popularity, how='left', on='item')

        ratedset = tuple([r.item_id for r in ratings])
        seed = hash(ratedset) % (2**32)

        candidates = preds[preds['count'] >= min_rating_count]
        candidates.index = pd.Index(candidates['item'].values)

        if randomize:
            idxvec = np.array(candidates.index)
            np.random.seed(seed)
            np.random.shuffle(idxvec)
            candidates = candidates[candidates.index.isin(idxvec[:init_sample_size])]

        diverse_items: pd.DataFrame
        if algo == 'fishnet':
            diverse_items, dists = self.__fishingnet(candidates, num_rec)
            dists = sorted(dists, key=lambda x: x[1])
            dists_n_idx = [item[0] for item in dists[:num_rec]]
            diverse_items = diverse_items[diverse_items['item'].isin(dists_n_idx)]
        elif algo == 'single_linkage':
            # sort the base on the score and pick top n
            candidates.sort_values(by='score', ascending=False, inplace=True)
            candlen = len(candidates)
            midstart = int(candlen / 2) - int(init_sample_size / 2)
            midend = int(candlen / 2) + int(init_sample_size / 2)
            # Get top n, bottom n, and middle n
            topn_user = candidates.head(init_sample_size).copy()
            botn_user = candidates.tail(init_sample_size).copy()
            midn_user = candidates.iloc[midstart:midend].copy()

            candidates = pd.concat([topn_user, botn_user, midn_user]).drop_duplicates()
            diverse_items = self.__single_linkage_clustering(candidates, num_rec)
        elif algo == 'random':
            diverse_items = candidates if randomize else candidates.sample(n=num_rec, random_state=seed)
        elif algo == 'fishnet + single_linkage':
            diverse_items, _ = self.__fishingnet(candidates, init_sample_size)
            diverse_items = self.__single_linkage_clustering(diverse_items, num_rec)
        else:
            diverse_items = candidates

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

    def predict_reference_items(
        self,
        ratings: list[MovieLensRatingSchema],
        num_rec: int,
        user_id: str,
        init_sample_size: int = 500,
        min_rating_count: int = 50,
    ) -> list[PrefVizItem]:
        distance_method = 'cosine'
        k = 200  # number of neighboars ot use as candidates

        preds = self.get_prediction(ratings, user_id)

        umat = self.model.user_features_
        users = self.model.user_index_

        u_feat = get_user_feature_from_biasedMF(self.model, preds['score'])
        knn = RSSABase._find_neighbors(self, umat, users, u_feat, distance_method, k)

        neighbors = knn['user'].tolist()
        rating_data = pd.read_csv(get_rating_data_path())

        neighbor_ratings_for_target_items = rating_data[
            (rating_data['user_id'].isin(neighbors)) & (rating_data['movie_id'].isin(preds['item']))
        ]

        average_neighbor_ratings = neighbor_ratings_for_target_items.groupby('movie_id')['rating'].mean()

        merged_preds = pd.merge(preds, average_neighbor_ratings, how='left', left_on='item', right_index=True)
        merged_preds = pd.merge(merged_preds, self.item_popularity, how='left', on='item')
        merged_preds = merged_preds.rename(columns={'rating': 'ave_score'})

        merged_preds.dropna(inplace=True)
        candidates = merged_preds[merged_preds['count'] >= min_rating_count]
        candidates.index = pd.Index(candidates['item'].values)

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
        ticks = [1]  # we start from 1 because there is no rating 0
        step = (n - 1) / nb
        for i in range(nb):
            ticks.append(ticks[i] + step)

        return ticks

    def scale_grid(self, minval, maxval, num_divisions):
        ticks = [minval]
        step = (maxval - minval) / num_divisions
        for i in range(num_divisions):
            ticks.append(ticks[i] + step)

        grid = list(itertools.product(ticks, ticks))
        grid = np.asarray(grid, dtype=np.float64)

        return grid

    def __convexhull(self, candidates):
        candidates_vector = candidates[['score', 'ave_score']].to_numpy()
        # TODO implement convex hull

    def __fishingnet(self, candidates: pd.DataFrame, n: int = 80) -> Tuple[pd.DataFrame, list[tuple]]:
        candidates_vector = candidates[['score', 'ave_score']].to_numpy()
        grid = self.scale_grid(minval=1, maxval=5, num_divisions=16)

        diverse_items = []

        # Greedy algorithm
        grid_members = {}
        for point in grid:
            dist = np.sum(np.abs(candidates_vector - point), axis=1)
            idx_shortest_dist = np.argmin(dist)
            candidates_vector = np.delete(candidates_vector, idx_shortest_dist, axis=0)

            item_idx = candidates.index[int(idx_shortest_dist)]
            val_shortest_dist = dist[idx_shortest_dist]

            grid_members[tuple(point)] = item_idx
            diverse_items.append((item_idx, val_shortest_dist))

        return candidates[candidates['item'].isin(grid_members.values())], diverse_items

    def __single_linkage_clustering(self, candidates: pd.DataFrame, n: int = 80):
        """
        Perform single linkage clustering on the candidates
        :param candidates: DataFrame containing the candidates
                columns: [
                        'item',
                        'score',
                        'ave_score',
                        'ave_discounted_score',
                        'count', 'rank'
                ]
        :param n: number of clusters
        """

        _candidates = candidates.copy()

        # This is weird, but a DataFrame row essentially behaved like a dict
        # score_avescore: Callable[[dict[str, float]], Tuple[float, float]]
        # score_avescore = lambda x: (x['score'], x['ave_score'])

        def unzip_scores(x):
            return (x['score'], x['ave_score'])

        _candidates['grid_idx'] = _candidates.apply(unzip_scores, axis=1)

        G = nx.Graph()
        G.add_nodes_from(_candidates['grid_idx'].values)

        # Add edges based on the distance between the nodes
        for node1 in G.nodes:
            for node2 in G.nodes:
                if node1 != node2:
                    # city block distance
                    dist = np.sum(np.abs(np.array(node1) - np.array(node2)))

                    # Euclidean distance
                    G.add_edge(node1, node2, weight=dist)

        tree = nx.minimum_spanning_tree(G)

        k = n  # Delete the costliest edge and make two graphs
        edges = list(tree.edges(data=True))
        edges.sort(key=lambda x: x[2]['weight'], reverse=True)
        while k >= 1:
            edge = edges[n - k]
            tree.remove_edge(edge[0], edge[1])
            k -= 1

        for i, cluster in enumerate(nx.connected_components(tree)):
            if len(cluster) > 1:
                clusternodes = list(cluster)
                # take the middle node
                minx = min(clusternodes, key=lambda x: x[0])
                maxx = max(clusternodes, key=lambda x: x[0])
                miny = min(clusternodes, key=lambda x: x[1])
                maxy = max(clusternodes, key=lambda x: x[1])

                mid = (minx[0] + maxx[0]) / 2, (miny[1] + maxy[1]) / 2
                cvec = np.array([np.array(c) for c in clusternodes])

                dist2mid = np.sum(np.abs(cvec - np.array(mid)), axis=1)
                closest2mid = np.argmin(dist2mid)
                midnode = clusternodes[closest2mid]
                row = _candidates[_candidates['grid_idx'] == (midnode[0], midnode[1])]
                _candidates.loc[row.index, 'cluster'] = i
            else:
                # take the only node
                node = cluster.pop()
                row = _candidates[_candidates['grid_idx'] == node]
                _candidates.loc[row.index, 'cluster'] = i

        return _candidates[_candidates['cluster'].notnull()]

    def scale_and_label(self, items, new_min=1, new_max=5):
        scaled_items = items.copy()
        scaled_items.rename(columns={'ave_score': 'community', 'score': 'user'}, inplace=True)
        # Label the items based on the global average
        global_avg = np.mean([np.median(scaled_items['community']), np.median(scaled_items['user'])])

        def label(row):
            row['community_label'] = 1 if row['community'] >= global_avg else 0
            row['user_label'] = 1 if row['user'] >= global_avg else 0
            return row

        labeled_items = scaled_items.apply(label, axis=1)

        labeled_items = labeled_items.astype(
            {'item': 'int64', 'count': 'int64', 'rank': 'int64', 'community_label': 'int64', 'user_label': 'int64'}
        )
        avg_comm_score = np.mean(labeled_items['community'])
        avg_user_score = np.mean(labeled_items['user'])

        return labeled_items, avg_comm_score, avg_user_score
