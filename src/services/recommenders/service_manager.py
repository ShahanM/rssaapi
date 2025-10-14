import logging
from typing import cast

from services.recommenders.asset_loader import load_or_get_asset_bundle

from .alt_rec_service import AlternateRS
from .pref_com_service import PreferenceCommunity
from .pref_viz_service import PreferenceVisualization

log = logging.getLogger(__name__)

IMPLICIT_MODEL_PATH = 'ml32m'
BIASED_MODEL_PATH = 'ml32m-biased'


REGISTERED_SERVICES: dict[str, object] = {}


def _safe_init_service(service_key: str, path: str, service_class: type):
    global REGISTERED_SERVICES

    shared_bundle = load_or_get_asset_bundle(path)

    if shared_bundle is None:
        REGISTERED_SERVICES[service_key] = None
        return

    instance = service_class(asset_bundle=shared_bundle)

    REGISTERED_SERVICES[service_key] = instance
    print(f'INFO: {service_key} initialized successfully.')


def init_recommender_services():
    _safe_init_service('prefcom', IMPLICIT_MODEL_PATH, PreferenceCommunity)
    _safe_init_service('altrec', IMPLICIT_MODEL_PATH, AlternateRS)
    _safe_init_service('prefviz', BIASED_MODEL_PATH, PreferenceVisualization)  # Loads Bundle 2


async def get_prefcom_service() -> PreferenceCommunity:
    """Dependency injector for the PrefCom model service."""
    instance = REGISTERED_SERVICES.get('prefcom')

    if instance is None:
        raise RuntimeError('PrefComService not initialized. Startup failed.')
    return cast(PreferenceCommunity, instance)


async def get_altrec_service() -> AlternateRS:
    """Dependency injector for the AltRecs model service."""
    instance = REGISTERED_SERVICES.get('altrec')

    if instance is None:
        raise RuntimeError('AlternateRS not initialized. Startup failed.')
    return cast(AlternateRS, instance)
