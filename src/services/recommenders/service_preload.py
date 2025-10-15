import logging
from typing import cast

from .alt_rec_service import AlternateRS
from .pref_com_service import PreferenceCommunity
from .pref_viz_service import PreferenceVisualization

log = logging.getLogger(__name__)

IMPLICIT_MODEL_PATH = 'ml32m'
BIASED_MODEL_PATH = 'ml32m-biased'


try:
    PREFCOM_SERVICE_INSTANCE = PreferenceCommunity(IMPLICIT_MODEL_PATH)
    print('INFO: PREFCOM_SERVICE_INSTANCE loaded globally.')
except Exception as e:
    print(f'CRITICAL ERROR loading PrefCom: {e}')
    PREFCOM_SERVICE_INSTANCE = None

try:
    PREFVIZ_SERVICE_INSTANCE = PreferenceVisualization(BIASED_MODEL_PATH)
    print('INFO: PREFVIZ_SERVICE_INSTANCE loaded globally.')
except Exception as e:
    print(f'CRITICAL ERROR loading PrefViz: {e}')
    PREFVIZ_SERVICE_INSTANCE = None


async def get_prefcom_service() -> PreferenceCommunity:
    """Dependency injector for the PrefCom model service."""
    if PREFCOM_SERVICE_INSTANCE is None:
        raise RuntimeError('PrefComService not initialized. Startup failed.')
    return cast(PreferenceCommunity, PREFCOM_SERVICE_INSTANCE)


async def get_prefviz_service() -> PreferenceVisualization:
    """Dependency injector for the PrefViz model service."""
    if PREFVIZ_SERVICE_INSTANCE is None:
        raise RuntimeError('PrefVizService not initialized. Startup failed.')
    return cast(PreferenceVisualization, PREFVIZ_SERVICE_INSTANCE)


async def get_alt_rec_service() -> AlternateRS:
    """Dependency injector for the RSSA alternate recommendations model service."""
    if IMPLICIT_MODEL_PATH is None:
        raise RuntimeError('AltRecService not intialized. Startup failed.')
    return cast(AlternateRS, IMPLICIT_MODEL_PATH)
