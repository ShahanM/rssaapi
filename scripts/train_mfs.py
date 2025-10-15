"""
RSSA Matrix Factorization Model Training Script (MF)

This script trains and serializes LensKit Matrix Factorization (ALS) models
for the Recommender System for Study Analysis (RS:SA) project.
It includes data pre-processing (discounting popular items) and generates
auxiliary baselines and artifacts (Annoy index, popularity stats).
----
File: train_mf.py
Project: RS:SA Recommender System (Clemson University)
Created Date: Saturday, 11th October 2025
Author: Mehtab 'Shahan' Iqbal
Affiliation: Clemson University
----
Last Modified: Wednesday, 15th October 2025 2:28:32 pm
Modified By: Mehtab 'Shahan' Iqbal (mehtabi@clemson.edu)
----
Copyright (c) 2025 Clemson University
License: MIT License (See LICENSE.md)
# SPDX-License-Identifier: MIT License
"""

import argparse
import logging
import os
import pickle
import time
from typing import Optional, Union, cast

import numpy as np
import pandas as pd
from annoy import AnnoyIndex
from joblib import Memory
from lenskit.algorithms import als
from lenskit.algorithms.mf_common import MFPredictor
from pydantic import BaseModel

log = logging.getLogger(__name__)

try:
    import binpickle
except ImportError:
    log.warning('Warning: binpickle not installed. Falling back to pickle.')
    binpickle = None


def setup_logging(output_dir: str):
    """Configures the logger to write to console and a date-stamped file."""
    log.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    log_filename = time.strftime('training_%Y%m%d_%H%M%S.log')
    log_path = os.path.join(output_dir, log_filename)

    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    log.info('Logging configured successfully. Output directed to console and file.')


cachedir = '.cache'
if not os.path.exists(cachedir):
    os.makedirs(cachedir)
memory = Memory(cachedir, verbose=1)


class Config(BaseModel):
    data_path: str
    model_path: str
    algo: str
    item_popularity: bool
    ave_item_score: bool
    cluster_index: bool
    ratings_index: bool
    resample_count: int


def _get_model_path(model_path: str) -> str:
    base_file = os.path.join(model_path, 'model')
    return f'{base_file}.bpk' if binpickle else f'{base_file}.pkl'


@memory.cache
def load_training_data(data_path):
    ratings_train = pd.read_csv(data_path)
    col_rename_dict = {}
    if 'user_id' in ratings_train:
        col_rename_dict['user_id'] = 'user'
    elif 'userId' in ratings_train:
        col_rename_dict['userId'] = 'user'
    if 'movie_id' in ratings_train:
        col_rename_dict['movie_id'] = 'item'
    elif 'movieId' in ratings_train:
        col_rename_dict['movieId'] = 'item'

    ratings_train = ratings_train.rename(columns=col_rename_dict)

    return ratings_train


def load_training_data_npz(data_path):
    """
    load the pre-saved npz file of the movie ratings
    """
    model_loaded = np.load(data_path)
    data = model_loaded['dataset']
    trainset = pd.DataFrame(data, columns=['user', 'item', 'rating', 'timestamp'])
    trainset = trainset.astype({'user': int, 'item': int, 'rating': float, 'timestamp': int})

    return trainset


def _train_mf_model(training_data: pd.DataFrame, algo: str) -> MFPredictor:
    model = None
    if algo == 'implicit':
        model = als.ImplicitMF(20, iterations=10, method='lu', use_ratings=True, save_user_features=True)
    elif algo == 'explicit':
        model = als.BiasedMF(20)

    if model is None:
        raise ValueError(f'Invalid algo: {algo}')
    model.fit(training_data)

    return model


def _train_resampled_models(
    training_data: pd.DataFrame, algo: str, resample_count: int, output_dir: str, alpha: float = 0.5
):
    sample_size = int(training_data.shape[0] * alpha)
    log.info(f'Training {resample_count} resampled models')
    start = time.time()

    for i in range(resample_count):
        log.info(f'Training resampled model {i + 1}')

        sample = training_data.sample(n=sample_size, replace=False)
        model = _train_mf_model(sample, algo)
        log.info(
            f'Serializing the trained model {i + 1} of {resample_count} \
            to disk.'
        )
        output_filename = f'{output_dir}/resampled_model_{i + 1}'
        output_file = f'{output_filename}.bpk' if binpickle else f'{output_filename}.pkl'
        if binpickle:
            binpickle.dump(model, output_file)
        else:
            with open(output_file, 'wb') as f:
                pickle.dump(model, f)

    end = time.time() - start
    log.info('Resampled models trained.')
    log.info(f'Time spent: {end:.2f}')


def _pre_aggregate_user_history(training_data: pd.DataFrame, output_path: str):
    """
    Aggregates the large training data into a compact, serializable DataFrame
    using vectorized operations for speed.
    """
    log.info('Building history look up table')

    # Group by user and aggregate item and rating columns into lists
    # This result (user_history_df) has the lists we need.
    user_history_df = (
        training_data.groupby('user')
        .agg(
            # The result columns are named 'rated_items' and 'ratings'
            rated_items=('item', list),
            ratings=('rating', list),
        )
        .reset_index()
    )

    # Vectorized Combination of Lists
    # We use numpy.vstack and then convert the array structure to a list of tuples
    # and assign it back to a column. This is much faster than itertuples.
    user_history_df['history_tuples'] = [
        list(zip(items, ratings)) for items, ratings in zip(user_history_df['rated_items'], user_history_df['ratings'])
    ]

    final_history_df = user_history_df[['user', 'history_tuples']]
    final_history_df.to_parquet(output_path, compression='snappy')

    log.info(f'User history lookup table saved to: {output_path} (Compressed)')


def _get_exact_mf_model(model: MFPredictor) -> Optional[Union[als.BiasedMF, als.ImplicitMF]]:
    if isinstance(model, als.BiasedMF):
        model = cast(als.BiasedMF, model)
    elif isinstance(model, als.ImplicitMF):
        model = cast(als.ImplicitMF, model)
    else:
        log.warning('Could not build Annoy index, model type unknown.')
        return None

    return model


def _compute_ave_item_scores(
    model: MFPredictor, training_data: pd.DataFrame, item_popularity: pd.DataFrame, alpha: float = 0.2
):
    """
    Computes the predicted average score for every item across the entire user population
    and calculates a corresponding popularity-discounted score.

    This function iterates through all users in the training set, uses the trained
    MF model to generate predictions for all items, and maintains a running mean
    of these predicted scores.

    Args:
        model (MFPredictor): The trained LensKit model object (MF model).
        training_data (pd.DataFrame): The pre-processed and discounted training data
                                        (used only to extract the list of unique users and items).
        item_popularity (pd.DataFrame): DataFrame containing item statistics, specifically
                                        the 'count' and 'rank_popular' columns, used for
                                        calculating the discounting penalty.
        alpha (float, optional): The weighting factor used to apply the popularity penalty
                                to the scores. Defaults to 0.2.

    Returns:
        pd.DataFrame: A DataFrame indexed by item containing two running averages:
                    - 'ave_score': The raw average predicted rating for the item
                                    across all users (the model-based baseline).
                    - 'ave_discounted_score': The predicted score penalized by
                                                item popularity.

    """
    start = time.time()
    log.info('Starting vectorized computation of average item scores...')

    model_instance = _get_exact_mf_model(model)
    if model_instance is None:
        log.error('Failed to get MF model instance for vectorization.')
        return pd.DataFrame(columns=['item', 'ave_score', 'ave_discounted_score'])

    global_bias = getattr(model_instance, 'bias', 0.0)
    user_features = model_instance.user_features_
    item_features = model_instance.item_features_
    item_index = model_instance.item_index_

    if user_features is None:
        return
    mean_user_features = user_features.mean(axis=0)

    core_projection_means = mean_user_features @ item_features.T
    ave_scores_vector = global_bias + core_projection_means

    ave_scores_df = pd.DataFrame({'item': item_index, 'ave_score': ave_scores_vector})

    max_count = item_popularity['count'].max()
    num_digits = len(str(int(max_count))) if max_count > 0 else 1
    discounting_factor = 10**num_digits

    ave_scores_df = pd.merge(ave_scores_df, item_popularity, how='left', on='item')
    ave_scores_df['ave_discounted_score'] = ave_scores_df['ave_score'] - alpha * (
        ave_scores_df['count'] / discounting_factor
    )

    log.info(f'Time spent (vectorized): {(time.time() - start):.4f}s. Calculated scores for {len(item_index)} items.')

    return ave_scores_df[['item', 'ave_score', 'ave_discounted_score']]


@memory.cache
def _compute_observed_item_mean(training_data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes the observed mean rating and rating count for every unique item
    in the training data.

    Args:
        training_data (pd.DataFrame): DataFrame containing user interactions,
                                    expected columns: ['user', 'item', 'rating'].

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            1. ave_scores_df (DataFrame with item and ave_score).
            2. item_popularity (DataFrame with item and count).
    """

    item_stats = training_data.groupby('item')['rating'].agg(['mean', 'count'])
    item_stats = item_stats.reset_index()

    item_stats['rank_popular'] = item_stats['count'].rank(method='min', ascending=False).astype(int)
    item_stats['rank_quality'] = item_stats['mean'].rank(method='min', ascending=False).astype(int)

    item_popularity = item_stats[['item', 'count', 'rank_popular', 'rank_quality']]
    ave_scores_df = item_stats[['item', 'mean']].rename(columns={'mean': 'ave_score'})
    ave_scores_df['ave_discounted_score'] = np.nan

    return ave_scores_df, item_popularity


def _create_annoy_index(user_factors: np.ndarray, user_index: pd.Index, output_path: str, n_trees: int = 50):
    """
    Creates and saves an Annoy index from the user latent factor matrix.

    Args:
        user_factors (np.ndarray): The User Latent Factor Matrix (P matrix).
        user_index (pd.Index): The Pandas Index mapping internal IDs (0..N) to external user IDs.
        output_path (str): File path to save the index.
        n_trees (int): Number of trees to build (higher = better precision, slower build).
    """

    dims = user_factors.shape[1]
    index = AnnoyIndex(dims, 'angular')

    for i, vector in enumerate(user_factors):
        index.add_item(i, vector)

    index.build(n_trees)
    index.save(output_path)
    user_map = pd.Series(user_index.values, index=np.arange(len(user_index)), name='user_id')

    user_map.to_csv(f'{output_path}_map.csv', header=True, index_label='internal_id')

    log.info(f'Annoy index built and saved to {output_path}')


@memory.cache
def _discount_popular_item_ratings(
    input_data: pd.DataFrame, items_popularity: pd.DataFrame, bias_factor: float = 0.4
) -> pd.DataFrame:
    """
    Penalizes the popular item by discounting the popular items rating by the bias_factor

    Args:
        input_data (pd.DataFrame): The training data with columsn ['user', 'item', 'rating', 'timestamp']
        items_popularity (pd.DataFrame): Item ranked according to their ratings count.
        bias_factor (float): The factor used to discount the popular ratings. Default to 0.4

    Returns:
        pd.DataFrame: DataFrame with the rating column replaced by the discounted ratings.
    """
    rpopularity = pd.merge(input_data, items_popularity, how='left', on='item')
    rpopularity['discounted_rating'] = rpopularity['rating'] * (1 - bias_factor / (2 * rpopularity['rank_popular']))
    rtrain = rpopularity[['user', 'item', 'discounted_rating', 'timestamp']]
    rtrain = rtrain.rename({'discounted_rating': 'rating'}, axis=1)

    return rtrain


def _get_model(config: Config) -> MFPredictor:  # Returns MFPredictor instance
    """
    Retrieves or trains the main Matrix Factorization model based on config flags.

    This implements conditional loading logic to ensure efficiency. If a trained
    model exists and retraining is not requested, the existing model is loaded.
    Otherwise, a full training run is initiated.
    """
    model_file = _get_model_path(config.model_path)
    model = None

    if os.path.exists(model_file) and not config.resample_count > 0:
        log.info(f'Existing model found: {model_file}. Loading trained model...')
        try:
            if binpickle:
                model = binpickle.load(model_file)
            else:
                with open(model_file, 'rb') as f:
                    model = pickle.load(f)
            log.info('Model loaded successfully.')
        except Exception as e:
            log.warning(f'Error loading model ({e}). Retraining will proceed.')
            model = None

    if model is None:
        log.info('Model not found or load failed. Initiating full training...')

        train_data = load_training_data(config.data_path)
        obs_ave_scores_df, items_popularity_df = _compute_observed_item_mean(train_data)
        discounted_train_data = _discount_popular_item_ratings(train_data, items_popularity_df)

        log.info(f'Training {config.algo} MF models')
        start = time.time()

        model = _train_mf_model(discounted_train_data, config.algo)

        end = time.time() - start
        log.info('MF model trained.')
        log.info(f'Time spent: {end:.2f}s')

        # 3. Serialize the newly trained model (only if trained)
        log.info('Serializing the trained model to disk.')
        if not os.path.exists(config.model_path):
            os.makedirs(config.model_path)

        if binpickle:
            binpickle.dump(model, model_file)
        else:
            with open(model_file, 'wb') as f:
                pickle.dump(model, f)

    return model


def _main(config: Config):
    """
    Main execution function for the Matrix Factorization (MF) training script.

    This function conditionally retrieves or trains the main model and then
    executes all requested post-processing and analysis steps.
    """
    model = _get_model(config)

    if model is None:
        log.error('ERROR: Could not load or train model. Skipping post-processing.')
        return

    train_data = load_training_data(config.data_path)
    obs_ave_scores_df, items_popularity_df = _compute_observed_item_mean(train_data)
    discounted_train_data = _discount_popular_item_ratings(train_data, items_popularity_df)

    if config.item_popularity:
        log.info('Saving the item popularity as a csv file')
        items_popularity_df.to_csv(f'{config.model_path}/item_popularity.csv', index=False)

    if config.resample_count > 0:
        _train_resampled_models(discounted_train_data, config.algo, config.resample_count, config.model_path)

    if config.ave_item_score:
        log.info('Computing the average model item scores')
        scores_df = _compute_ave_item_scores(model, discounted_train_data, items_popularity_df)
        if scores_df is not None:
            log.info('Saving the average model item scores as a csv file')
            scores_df.to_csv(f'{config.model_path}/averaged_item_score.csv', index=False)

        log.info('Saving the average observed item scores as a csv file')
        obs_ave_scores_df.to_csv(f'{config.model_path}/obs_ave_item_score.csv', index=False)

    if config.cluster_index or config.ratings_index:
        log.info('Building and saving the Annoy index')
        model_instance = _get_exact_mf_model(model)
        if model_instance is not None:
            user_mat = model_instance.user_features_
            user_index = model_instance.user_index_

            if user_mat is not None and user_index is not None:
                _create_annoy_index(user_mat, user_index, f'{config.model_path}/annoy_index')

    if config.ratings_index:
        _pre_aggregate_user_history(discounted_train_data, f'{config.model_path}/user_history_lookup.parquet')

    log.info('Done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=(
            'Train Matrix Factorization (MF) models for the RSSA (Recommender System for Study Analysis) '
            'project. Generates primary and baseline models for evaluation.'
        )
    )
    # --- Required Arguments ---
    parser.add_argument(
        '-d',
        '--data_path',
        type=str,
        required=True,
        help=(
            'Path to the CSV file containing the raw user interaction data. '
            'Expected columns include: [user_id, movie_id, rating, timestamp].'
        ),
    )
    parser.add_argument(
        '-o',
        '--model_path',
        type=str,
        required=True,
        help=(
            'Path to the output directory where the trained pipeline, serialized model, '
            'and analysis files will be saved.'
        ),
    )

    # --- Algorithm Selection ---
    parser.add_argument(
        '-a',
        '--algo',
        type=str,
        required=False,
        default='implicit',
        choices=['implicit', 'biased'],
        help=(
            'Specifies the Matrix Factorization algorithm type to train. '
            'Choose "implicit" for Implicit ALS (optimizing preference/confidence) or '
            '"biased" for Biased MF (optimizing explicit rating prediction).'
        ),
    )

    # --- Optional Analysis Flags ---
    parser.add_argument(
        '--item_popularity',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            'If set, calculates the observed popularity statistics (count and rank) of all items '
            'and saves the results as a CSV file.'
        ),
    )
    parser.add_argument(
        '--ave_item_score',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            'If set, computes and saves two item score baselines: '
            '1) the global observed mean rating for each item, and '
            '2) the model-predicted average score for each item across all users.'
        ),
    )
    parser.add_argument(
        '--cluster_index',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            'If set, builds and saves an Annoy index over the final user latent factor matrix (P matrix). '
            ' This enables extremely fast K-NN lookups for the warm-start prediction baseline.'
        ),
    )

    parser.add_argument(
        '--ratings_index',
        required=False,
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            'If set, aggregates the large training data into a compact, serializable DataFrame. '
            ' This enables a fast an efficient way to look up ratings from the training data at runtime.'
        ),
    )

    # --- Advanced Training Parameters ---
    parser.add_argument(
        '-r',
        '--resample_count',
        type=int,
        required=False,
        default=0,
        help=(
            'The number of additional resampled models to train for robust evaluation (e.g., bootstrapping). '
            'If set to N > 0, N models are trained on distinct subsets of the training data '
            'and serialized individually.'
        ),
    )
    args = parser.parse_args()

    setup_logging(args.model_path)

    run_config = Config(
        data_path=args.data_path,
        model_path=args.model_path,
        algo=args.algo,
        item_popularity=args.item_popularity,
        ave_item_score=args.ave_item_score,
        cluster_index=args.cluster_index,
        ratings_index=args.ratings_index,
        resample_count=args.resample_count,
    )
    log.info('Starting model training script.')
    _main(run_config)
    log.info('Script execution finished.')

    # ieRS
    # --algo 'implicit'
    # --item_popularity
    # --ave_item_score

    # alt algo
    """
    python algs/train/train_models.py \
    -d ~/zugzug/data/movies/ml-32m/ratings.csv \
    -o algs/models/ml32m/ \
    -a implicit \
    --item_popularity \
    --ave_item_score \
    --cluster_index \
    --resample_count 20
    """

    # pref viz
    # --algo 'biased'
    # --item_popularity
    # --ave_item_score
    """
    python algs/train/train_models.py \
    -d ~/zugzug/data/movies/ml-32m/ratings.csv \
    -o algs/models/ml32m-biased/ \
    -a biased \
    --item_popularity \
    --ave_item_score \
    --cluster_index
    """
