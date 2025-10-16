import logging

from services.recommenders.asset_loader import load_and_cache_asset_bundle

from .alt_rec_service import AlternateRS
from .pref_com_service import PreferenceCommunity
from .pref_viz_service import PreferenceVisualization

log = logging.getLogger(__name__)

IMPLICIT_MODEL_PATH = 'ml32m-new'
BIASED_MODEL_PATH = 'ml32m-biased'


def get_prefcom_service() -> PreferenceCommunity:
    """
    Dependency function: Retrieves the PrefCom service instance, triggering
    the lazy loading of the shared model assets if not already cached in this process.
    """
    bundle = load_and_cache_asset_bundle(IMPLICIT_MODEL_PATH)
    return PreferenceCommunity(asset_bundle=bundle)


async def get_altrec_service() -> AlternateRS:
    """
    Dependency function: Retrieves the AltRecs service instance, triggering
    the lazy loading of the shared model assets if not already cached in this process.
    """

    bundle = load_and_cache_asset_bundle(IMPLICIT_MODEL_PATH)
    return AlternateRS(asset_bundle=bundle)
