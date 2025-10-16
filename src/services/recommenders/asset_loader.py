import logging
from functools import lru_cache
from typing import cast

import binpickle
import pandas as pd
from annoy import AnnoyIndex
from lenskit.als import ALSBase
from lenskit.pipeline.nodes import ComponentInstanceNode

from core.config import MODELS_DIR

log = logging.getLogger(__name__)


class ModelAssetBundle:
    """Container for all unique, pre-loaded assets (Pipeline, Annoy, History Map)
    associated with a single model file path."""

    def __init__(self, model_folder: str):
        self.path = MODELS_DIR / model_folder
        self.item_popularity = pd.read_csv(self.path / 'item_popularity.csv')
        self.ave_item_score = pd.read_csv(self.path / 'averaged_item_score.csv')

        self.pipeline = self._load_pipeline_asset()
        self.scorer: ALSBase = self._get_trained_scorer()
        self.annoy_index, self.user_map_lookup = self._load_annoy_assets_asset()
        self.history_lookup_map = self._load_history_lookup_asset()

    def _load_pipeline_asset(self):
        return binpickle.load(f'{self.path}/model.bpk')

    def _get_trained_scorer(self) -> ALSBase:
        """
        Extracts the trained Scorer instance (ALSBase) from the loaded Pipeline.
        """
        pipeline_component: ComponentInstanceNode = cast(ComponentInstanceNode, self.pipeline.node('scorer'))
        scorer: ALSBase = cast(ALSBase, pipeline_component.component)

        return scorer

    def _load_annoy_assets_asset(self):
        """Loads the pre-built Annoy index and the ID mapping table."""

        annoy_index_path = f'{self.path}/annoy_index'
        user_map_path = f'{annoy_index_path}_map.csv'

        user_feature_vector = self.scorer.user_embeddings
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

        user_map_df = pd.read_csv(user_map_path, index_col=0)

        return index, user_map_df.iloc[:, 0].to_dict()

    def _load_history_lookup_asset(self) -> pd.Series:
        """Loads the compact user history Parquet file and converts it to a dict/Series for quick lookup."""
        history_path = f'{self.path}/user_history_lookup.parquet'

        history_df = pd.read_parquet(history_path)

        return history_df.set_index('user_id')['history_tuples']


@lru_cache(maxsize=1)
def load_and_cache_asset_bundle(model_path: str) -> ModelAssetBundle:
    """
    Loads all heavy assets (Pipeline, Annoy, History Map) for a given model_path.

    The result is cached in memory using LRU, ensuring the heavy I/O only
    occurs once per unique file path per worker process lifetime.
    """
    print(f'INFO: CACHE MISS. Loading heavy bundle from disk for: {model_path}')

    return ModelAssetBundle(model_path)


def get_asset_bundle_dependency(model_path: str) -> ModelAssetBundle:
    """
    Dependency function that looks up the Asset Bundle instance.
    The bundle is loaded lazily and retrieved from cache on subsequent calls.
    """
    return load_and_cache_asset_bundle(model_path)
