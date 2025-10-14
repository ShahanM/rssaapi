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
Last Modified: Sunday, 12th October 2025 12:48:12 am
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
from typing import cast

import numpy as np
import pandas as pd
from annoy import AnnoyIndex
from joblib import Memory
from lenskit import Pipeline, score
from lenskit.als import ALSBase, BiasedMFConfig, BiasedMFScorer, ImplicitMFConfig, ImplicitMFScorer
from lenskit.data import RecQuery, from_interactions_df
from lenskit.pipeline import predict_pipeline
from lenskit.pipeline.nodes import ComponentInstanceNode
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


def _train_mf_model(training_data: pd.DataFrame, algo: str) -> Pipeline:
    """
    Constructs, configures, and trains a Matrix Factorization (MF) pipeline
    using the modern LensKit Component architecture.

    The function selects the appropriate Scorer (Implicit or Biased) based on the
    'algo' argument, embeds the configuration (embedding size, user embeddings),
    and trains the resulting pipeline on the provided data.

    Args:
        training_data (pd.DataFrame): The pre-processed and discounted training data.
        algo (str): Specifies the type of MF algorithm: 'implicit' (for ImplicitMF)
                    or 'biased' (for BiasedMF).

    Returns:
        Pipeline: The trained LensKit Pipeline object, which contains the fitted
                Scorer instance and is ready for prediction and factor extraction.

    Raises:
        ValueError: If the provided 'algo' string is not one of the valid choices.
    """
    config = None

    if algo == 'implicit':
        config = ImplicitMFConfig(embedding_size=20, user_embeddings=True, use_ratings=True)
        scorer = ImplicitMFScorer(config=config)
    elif algo == 'biased':
        config = BiasedMFConfig(embedding_size=20, user_embeddings=True)
        scorer = BiasedMFScorer(config=config)
    else:
        raise ValueError(f'Invalid algo: {algo}')

    pipeline = predict_pipeline(scorer=scorer, name=f'rssa-{algo}')
    dataset = from_interactions_df(training_data, user_col='user', item_col='item', rating_col='rating')
    pipeline.train(dataset)

    return pipeline


def _train_resampled_models(
    training_data: pd.DataFrame, algo: str, resample_count: int, output_dir: str, alpha: float = 0.5
):
    """
    Trains multiple Matrix Factorization (MF) models on resampled subsets of the data
    for robust evaluation, such as bootstrapping or ensemble creation.

    Each model is trained on a unique, non-overlapping subset of the data and
    serialized separately.

    Args:
        training_data (pd.DataFrame): The full, pre-processed training data (with
                                    discounted ratings) from which samples are drawn.
        algo (str): The MF algorithm to use ('implicit' or 'biased').
        resample_count (int): The total number of resampled models to train.
        output_dir (str): The base directory to save the serialized models.
        alpha (float, optional): The fraction of the training data size to use for
                                each sample. Defaults to 0.5 (50%).

    Note:
        Models are serialized using binpickle (preferred) or pickle to individual files
        (e.g., 'resampled_model_1.bpk', 'resampled_model_2.bpk', etc.).
    """
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


def _compute_ave_item_scores(pipeline: Pipeline, training_data, item_popularity, alpha=0.2):
    """
    Computes the predicted average score for every item across the entire user population
    and calculates a corresponding popularity-discounted score.

    This function iterates through all users in the training set, uses the trained
    MF pipeline to generate predictions for all items, and maintains a running mean
    of these predicted scores.

    Args:
        pipeline (Pipeline): The trained LensKit Pipeline object (MF model).
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

    Note:
        The pipeline.score() function is used for prediction, and the process uses
        efficient running averages to avoid excessive memory usage.
    """
    items = training_data.item.unique()
    users = training_data.user.unique()

    discounting_factor = 10 ** len(f'{item_popularity["count"].max()}')

    start = time.time()

    ave_scores_df = pd.DataFrame(items, columns=['item'])
    ave_scores_df['ave_score'] = 0
    ave_scores_df['ave_discounted_score'] = 0

    calculated_users = -1
    for user in users:
        calculated_users += 1

        query = RecQuery(user_id=user)
        user_implicit_preds = score(pipeline, query, items)

        user_df = user_implicit_preds.to_df().reset_index()
        user_df.columns = ['item', 'score', 'rank']
        user_df = pd.merge(user_df, item_popularity, how='left', on='item')
        user_df['discounted_score'] = user_df['score'] - alpha * (user_df['count'] / discounting_factor)

        ave_scores_df['ave_score'] = (ave_scores_df['ave_score'] * calculated_users + user_df['score']) / (
            calculated_users + 1
        )

        ave_scores_df['ave_discounted_score'] = (
            ave_scores_df['ave_discounted_score'] * calculated_users + user_df['discounted_score']
        ) / (calculated_users + 1)

    log.info(f'Time spent:  {(time.time() - start):.2f}')

    return ave_scores_df


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


def _create_annoy_index(user_factors: np.ndarray, user_map: pd.Series, output_path: str, n_trees: int = 50):
    """
    Creates and saves an Annoy index from the user latent factor matrix.

    Args:
        user_factors (np.ndarray): The User Latent Factor Matrix (P matrix).
        user_map (pd.Series): Mapping from internal integer IDs to public user IDs.
        output_path (str): File path to save the index.
        n_trees (int): Number of trees to build (higher = better precision, slower build).
    """

    dims = user_factors.shape[1]
    index = AnnoyIndex(dims, 'angular')

    for i, vector in enumerate(user_factors):
        index.add_item(i, vector)

    index.build(n_trees)
    index.save(output_path)
    user_map.to_csv(f'{output_path}_map.csv', header=True)

    log.info(f'Annoy index built and saved to {output_path}')


def _get_pipeline_path(model_path: str) -> str:
    """Utility method to add the correct serialized extension."""
    base_file = f'{model_path}/model'
    return f'{base_file}.bpk' if binpickle else f'{base_file}.pkl'


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


def _get_pipeline(config: Config) -> Pipeline:
    """
    Retrieves or trains the main Matrix Factorization (MF) pipeline model.

    This function implements conditional logic to ensure efficiency: it attempts to
    load an existing serialized pipeline from disk if available and if a full retraining
    (resampling) is not requested. If the pipeline file is missing, the load fails,
    or a full retraining is required, a new model is trained using the provided data.

    Args:
        config (Config): The application configuration object containing parameters
                        like `model_path`, `data_path`, `algo`, and `resample_count`.

    Returns:
        Pipeline: The trained or loaded LensKit Pipeline object, ready for prediction
                    and post-analysis.
    """
    pipeline_file = _get_pipeline_path(config.model_path)
    pipeline = None
    if os.path.exists(pipeline_file) and not config.resample_count > 0:
        log.info(f'Existing pipeline found: {pipeline_file}. Loading trained model...')
        try:
            global binpickle
            if binpickle:
                import binpickle

                pipeline = binpickle.load(pipeline_file)
            else:
                with open(pipeline_file, 'rb') as f:
                    pipeline = pickle.load(f)
            log.info('Pipeline loaded successfully.')
        except Exception as e:
            log.info(f'Error loading pipeline: {e}. Retraining will proceed.')
            pipeline = None

    if pipeline is None:
        train_data = load_training_data(config.data_path)
        _, items_popularity_df = _compute_observed_item_mean(train_data)
        discounted_train_data = _discount_popular_item_ratings(train_data, items_popularity_df)

        log.info(f'Training {config.algo} MF models')
        start = time.time()

        pipeline = _train_mf_model(discounted_train_data, config.algo)

        end = time.time() - start
        log.info('MF model trained.')
        log.info(f'Time spent: {end:.2f}')

        log.info('Serializing the trained model to disk.')
        if not os.path.exists(config.model_path):
            os.makedirs(config.model_path)

        if binpickle:
            binpickle.dump(pipeline, pipeline_file)
        else:
            with open(pipeline_file, 'wb') as f:
                pickle.dump(pipeline, f)

    return pipeline


def _main(config: Config):
    """
    Main execution function for the Matrix Factorization (MF) training script.

    This function conditionally loads an existing trained model or initiates a full
    training run. It then performs all requested post-processing, analysis,
    and model saving based on the provided configuration flags.

    Args:
        config (Config): A Pydantic configuration object containing all necessary
                        parameters (data_path, algo, model_path, and boolean flags).

    Execution Flow:
        1. Model Retrieval: Attempts to load a serialized LensKit Pipeline from disk
            using '_get_pipeline()'. If the file is not found, or if resampling is requested,
            a new pipeline is trained using the discounted input data.
        2. Input Discounting: Calculates item popularity and uses the 'rank_popular'
            score to create a discounted training dataset (rtrain). This discounted data
            is used for training the MF model.
        3. Post-Processing (Conditional):
            - --item_popularity: Saves the observed item count and popularity rank.
            - --ave_item_score: Computes and saves two baselines: the observed mean rating
            and the model's predicted average item score.
            - --cluster_index: Extracts the trained user latent factor matrix (P matrix)
            from the pipeline and builds an Annoy index for fast runtime K-NN lookups.
            - -r / --resample_count: Initiates training of N additional models on sampled
            subsets of the data.
    """
    pipeline = _get_pipeline(config)

    if pipeline is None:
        log.error('ERROR: Could not load or train a pipeline. Skipping post-processing.')
        return

    if config.item_popularity:
        train_data = load_training_data(config.data_path)
        obs_ave_scores_df, items_popularity_df = _compute_observed_item_mean(train_data)

        log.info('Saving the item popularity as a csv file')
        items_popularity_df.to_csv(f'{config.model_path}/item_popularity.csv', index=False)

    if config.resample_count > 0:
        train_data = load_training_data(config.data_path)
        obs_ave_scores_df, items_popularity_df = _compute_observed_item_mean(train_data)
        discounted_train_data = _discount_popular_item_ratings(train_data, items_popularity_df)
        _train_resampled_models(discounted_train_data, config.algo, config.resample_count, config.model_path)

    if config.ave_item_score:
        train_data = load_training_data(config.data_path)
        obs_ave_scores_df, items_popularity_df = _compute_observed_item_mean(train_data)
        discounted_train_data = _discount_popular_item_ratings(train_data, items_popularity_df)
        log.info('Computing the average item scores')
        scores_df = _compute_ave_item_scores(pipeline, discounted_train_data, items_popularity_df)
        log.info('Saving the average model item scores as a csv file')
        scores_df.to_csv(f'{config.model_path}/averaged_item_score.csv', index=False)
        log.info('Saving the average observed item scores as a csv file')
        obs_ave_scores_df.to_csv(f'{config.model_path}/obs_ave_item_score.csv', index=False)

    if config.cluster_index:
        train_data = load_training_data(config.data_path)
        obs_ave_scores_df, items_popularity_df = _compute_observed_item_mean(train_data)
        discounted_train_data = _discount_popular_item_ratings(train_data, items_popularity_df)

        log.info('Building and saving the Annoy index')
        pipeline_component: ComponentInstanceNode = cast(ComponentInstanceNode, pipeline.node('scorer'))
        scorer: ALSBase = cast(ALSBase, pipeline_component.component)

        user_mat_tensor = scorer.user_features_
        if user_mat_tensor is not None:
            user_mat: np.ndarray = user_mat_tensor.cpu().detach().numpy()
            user_vocab = scorer.users_
            if user_vocab is not None and user_vocab.size > 0:
                external_ids_array = user_vocab.ids(None)
                internal_codes_array = np.arange(user_vocab.size, dtype=np.int32)
                user_map_series = pd.Series(
                    data=external_ids_array,
                    index=internal_codes_array,
                    name='user_id',
                )
                _create_annoy_index(user_mat, user_map_series, f'{config.model_path}/annoy_index')

    if config.ratings_index:
        train_data = load_training_data(config.data_path)
        obs_ave_scores_df, items_popularity_df = _compute_observed_item_mean(train_data)
        discounted_train_data = _discount_popular_item_ratings(train_data, items_popularity_df)
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
