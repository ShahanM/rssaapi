import logging
import uuid
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .apps.admin import main as admin
from .apps.demo import main as demo
from .apps.study import main as study
from .core.config import ROOT_PATH, configure_logging
from .middlewares.bad_request_logging import BadRequestLoggingMiddleware
from .middlewares.infostats import RequestHandlingStatsMiddleware
from .middlewares.logging import LoggingMiddleware
from .services.recommenders.service_manager import init_recommender_services

configure_logging()
log = logging.getLogger(__name__)


# log.info('Intializing recommender services')
# initialize_services(PREFCOM_MODEL_PATH, PREFVIZ_MODEL_PATH)
# @asynccontextmanager
# async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
#     yield
#     await clear_singleton_services()

init_recommender_services()
"""
FastAPI App
"""
app = FastAPI(
    root_path=ROOT_PATH,
    title='Recommender Systems for Self Actualization',
    version='0.4.0',
    # lifespan=lifespan,
    terms_of_service='https://rssa.recsys.dev/terms',
    docs_url=None,
    redoc_url=None,
    state={'CACHE': {}, 'CACHE_LIMIT': 100, 'queue': []},
    security=[{'Study ID': []}],
    json_encoders={
        uuid.UUID: lambda obj: str(obj),
        datetime: lambda dt: dt.isoformat(),
    },
)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    log.error(f'Validation Error for URL: {request.url}')
    try:
        body = await request.body()
        log.error(f'Request Body: {body.decode()}')
    except Exception:
        log.error('Could not parse request body.')
    log.error(f'Validation Errors: {exc.errors()}')
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={'detail': exc.errors()},
    )


"""
CORS Origins
"""
origins = [
    'http://localhost:3330',
    'http://localhost:3330/*',
    'http://localhost:3339',
    'http://localhost:3339/*',
    'http://localhost:3331',
    'http://localhost:3340',
    'http://localhost:3350',
    'http://localhost:3000',
    'http://localhost:3369',
]

app.mount('/study', study.api)
app.mount('/admin', admin.api)
app.mount('/demo', demo.api)

"""
Middlewares
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
# app.add_middleware(RequestHandlingStatsMiddleware)
# app.add_middleware(BadRequestLoggingMiddleware)
# app.add_middleware(LoggingMiddleware)


# @app.on_event('startup') # FIXME: Do not use on_event, look at the lifecycle documentation
# def load_assets():
#     global ANN_INDEX, USER_MAP_REV, MODEL

#     # 1. Load trained MF pipeline/model (required for latent vector calculation)
#     MODEL = binpickle.load('path/to/trained_pipeline.bpk')

#     # 2. Load Annoy Index
#     dims = MODEL.scorer.model.user_features_.shape[1]  # Or hardcode embedding size
#     ANN_INDEX = AnnoyIndex(dims, 'angular')
#     ANN_INDEX.load('path/to/user_factors.ann')

#     # 3. Load User Map (Reverse lookup: internal ID -> public ID)
#     user_map_df = pd.read_csv('path/to/user_factors.ann_map.csv', index_col=0, squeeze=True)
#     USER_MAP_REV = user_map_df.reset_index().set_index('0')['index']

#     # You also need the full training data for the final average calculation (Scenario 1)
#     # If using Scenario 2, you only need the latent matrix.


# Usage example
# def get_k_nearest_neighbors(new_user_profile_vector: np.ndarray, k: int = 50):
#     # 1. Find the k nearest neighbor internal IDs
#     # n=k, include_distances=False
#     internal_ids, _ = ANN_INDEX.get_nns_by_vector(new_user_profile_vector, k, include_distances=True)

#     # 2. Convert internal IDs back to public user IDs
#     public_user_ids = USER_MAP_REV.loc[internal_ids].tolist()

#     return public_user_ids


@app.get('/')
async def root():
    """
    Hello World!
    """
    return {'message': 'Hello World! Welcome to RSSA APIs!'}
