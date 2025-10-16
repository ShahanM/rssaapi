from functools import lru_cache
from typing import Optional, Union, cast

import binpickle
import pandas as pd
from annoy import AnnoyIndex
from lenskit.algorithms import als
from lenskit.algorithms.mf_common import MFPredictor

from core.config import MODELS_DIR

MFModelType = Union[als.BiasedMF, als.ImplicitMF]


class ModelAssetBundle:
    """Container for all unique, pre-loaded assets (Pipeline, Annoy, History Map)
    associated with a single model file path."""

    def __init__(self, model_folder: str):
        self.path = MODELS_DIR / model_folder
        self.item_popularity = pd.read_csv(self.path / 'item_popularity.csv')
        self.ave_item_score = pd.read_csv(self.path / 'averaged_item_score.csv')

        mf_model: MFPredictor = self._load_model_asset()
        model_instance: Optional[MFModelType] = self._get_typed_model_instance(mf_model)
        if model_instance is None:
            raise RuntimeError('Model was not loaded properly.')
        self.model: MFModelType = model_instance

        # self.annoy_index, self.user_map_lookup = self._load_annoy_assets_asset()
        # self.history_lookup_map = self._load_history_lookup_asset()

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

    def _load_history_lookup_asset(self) -> pd.Series:
        """Loads the compact user history Parquet file and converts it to a dict/Series for quick lookup."""
        history_path = f'{self.path}/user_history_lookup.parquet'

        history_df = pd.read_parquet(history_path)

        # Convert the DataFrame back to a Series indexed by user ID for O(1) lookup speed
        # The Series values are the list of (item_id, rating) tuples
        return history_df.set_index('user')['history_tuples']


# Cache: Maps model directory paths (str) to loaded AssetBundle instances
# _ASSET_CACHE: dict[str, ModelAssetBundle] = {}


# def load_or_get_asset_bundle(model_path: str) -> ModelAssetBundle:
#     """Ensures a full set of assets is loaded exactly once per unique path."""
#     if model_path in _ASSET_CACHE:
#         print(f'INFO: Asset bundle retrieved from cache: {model_path}')
#         return _ASSET_CACHE[model_path]

#     print(f'INFO: Loading new asset bundle (Pipeline, Annoy, History) from: {model_path}')
#     bundle = ModelAssetBundle(model_path)
#     _ASSET_CACHE[model_path] = bundle
#     return bundle


@lru_cache(maxsize=16)  # Cache up to 16 unique model bundles in memory
def load_and_cache_asset_bundle(model_path: str) -> ModelAssetBundle:
    """
    Loads all heavy assets (Pipeline, Annoy, History Map) for a given model_path.

    The result is cached in memory using LRU, ensuring the heavy I/O only
    occurs once per unique file path per worker process lifetime.
    """
    print(f'INFO: CACHE MISS. Loading heavy bundle from disk for: {model_path}')

    # The ModelAssetBundle.__init__ contains all the binpickle.load, Annoy.load, etc.
    # We assume ModelAssetBundle.__init__ is synchronous and handles the disk I/O.
    return ModelAssetBundle(model_path)


# --- The Dependency Function (The Final Injector) ---


def get_asset_bundle_dependency(model_path: str) -> ModelAssetBundle:
    """
    Dependency function that looks up the Asset Bundle instance.
    The bundle is loaded lazily and retrieved from cache on subsequent calls.
    """
    # Call the cached function with the unique file
    return load_and_cache_asset_bundle(model_path)
