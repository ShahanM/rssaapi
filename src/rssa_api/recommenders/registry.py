import os
from dataclasses import dataclass

from rssa_api.data.schemas.movie_schemas import (
    AdvisorMovieFormalRead,
    AdvisorMovieInformalRead,
    ERSMovieSchema,
    MovieDetailSchema,
    MovieSchema,
)

from .strategies import LambdaStrategy, LocalDevStrategy

LAMBDA_IMPLICIT = os.environ.get('LAMBDA_NAME_IMPLICIT', 'ImplicitMFRecsFunction')
LAMBDA_BIASED = os.environ.get('LAMBDA_NAME_BIASED', 'BiasedMFRecsFunction')
LAMBDA_EMOTION = os.environ.get('LAMBDA_NAME_IMPLICIT_ERS', 'ImplicitMFErsRecsFunction')


@dataclass
class StrategyManifest:
    """Defines the capabilities and boundaries of a recommendation algorithm."""

    strategy: LambdaStrategy | LocalDevStrategy
    domain: str
    id_field: str
    default_schema: str
    supported_schemas: set[str]
    variant: str | None = None


SCHEMA_REGISTRY = {
    'standard': ((MovieSchema,), 'movielens_id'),
    'standard_emotion': ((ERSMovieSchema,), 'movielens_id'),
    'detailed': ((MovieDetailSchema,), 'movielens_id'),
    'community_advisors': (
        {'formal': (AdvisorMovieFormalRead, MovieSchema), 'informal': (AdvisorMovieInformalRead, MovieSchema)},
        'movielens_id',
    ),  # Advisors don't need full details
    'community_comparison': ((MovieSchema,), 'movielens_id'),  # PrefViz doesn't need full details
    # 'book_standard': (BookSchema, 'isbn'), # A placeholder to remind me why I am maintain a registry
}

REGISTRY: dict[str, StrategyManifest] = {
    # ----------------------------------------------------------------------------
    # Implicit Models
    'implicit_recs_top_n': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'top_n'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard',
        supported_schemas={'standard', 'detailed'},
    ),
    'implicit_recs_discounted_top_n': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'discounted_top_n'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard',
        supported_schemas={'standard', 'detailed'},
    ),
    'controversial': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'controversial'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard',
        supported_schemas={'standard', 'detailed'},
    ),
    'hate': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'hate'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard',
        supported_schemas={'standard', 'detailed'},
    ),
    'hip': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'hip'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard',
        supported_schemas={'standard', 'detailed'},
    ),
    'no_clue': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'no_clue'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard',
        supported_schemas={'standard', 'detailed'},
    ),
    'low_div_comm_advisors_formal': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_IMPLICIT,
            payload_template={
                'path': 'community_advisors',
                'strategy': 'top_n',
            },
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='advisor',
        supported_schemas={'community_advisors'},
        variant='formal',
    ),
    'low_div_comm_advisors_informal': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_IMPLICIT,
            payload_template={
                'path': 'community_advisors',
                'strategy': 'top_n',
            },
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='advisor',
        supported_schemas={'community_advisors'},
        variant='informal',
    ),
    'high_div_no_comp_comm_advisors_formal': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_IMPLICIT,
            payload_template={
                'path': 'community_advisors',
                'strategy': 'diverse_n',
            },
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='advisor',
        supported_schemas={'community_advisors'},
        variant='formal',
    ),
    'high_div_no_comp_comm_advisors_informal': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_IMPLICIT,
            payload_template={
                'path': 'community_advisors',
                'strategy': 'diverse_n',
            },
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='advisor',
        supported_schemas={'community_advisors'},
        variant='informal',
    ),
    'high_div_comp_comm_advisors_formal': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_IMPLICIT,
            payload_template={
                'path': 'community_advisors',
                'strategy': 'compromised_diverse_n',
            },
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='advisor',
        supported_schemas={'community_advisors'},
        variant='formal',
    ),
    'high_div_comp_comm_advisors_informal': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_IMPLICIT,
            payload_template={
                'path': 'community_advisors',
                'strategy': 'compromised_diverse_n',
            },
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='advisor',
        supported_schemas={'community_advisors'},
        variant='informal',
    ),
    # ----------------------------------------------------------------------------
    # Biased Models
    'biased_recs_top_n': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_BIASED, payload_template={'path': 'top_n'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard',
        supported_schemas={'standard', 'detailed', 'community_comparison'},
    ),
    'biased_community_scored': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_BIASED, payload_template={'path': 'community_scored_predictions'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='prefviz',
        supported_schemas={'community_comparison', 'standard'},
    ),
    'biased_ann_predicted_community_scored': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_BIASED,
            payload_template={'path': 'community_scored_predictions', 'ave_score_type': 'nn_predicted'},
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='prefviz',
        supported_schemas={'community_comparison'},
    ),
    'biased_ann_observed_community_scored': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_BIASED,
            payload_template={'path': 'community_scored_predictions', 'ave_score_type': 'nn_observed'},
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='prefviz',
        supported_schemas={'community_comparison'},
    ),
    'biased_global_observed_community_scored': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_BIASED,
            payload_template={'path': 'community_scored_predictions', 'ave_score_type': 'global'},
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='prefviz',
        supported_schemas={'community_comparison'},
    ),
    # ----------------------------------------------------------------------------
    # Emotion Models
    'implicit_ers_top_n': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_EMOTION,
            payload_template={'path': 'emotions_diversified_recommendations', 'strategy': 'top_n'},
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard_emotion',
        supported_schemas={'standard_emotion'},
    ),
    'implicit_ers_diverse_n': StrategyManifest(
        strategy=LambdaStrategy(
            function_name=LAMBDA_EMOTION,
            payload_template={'path': 'emotions_diversified_recommendations', 'strategy': 'diverse_n'},
        ),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard_emotion',
        supported_schemas={'standard_emotion'},
    ),
}

"""
Local Development Overrides

The following endpoint is used by the Docker dev network.
"""
ENV = os.environ.get('ENV', 'production')

if ENV == 'development':
    LOCAL_ROUTE_MAP = {
        LAMBDA_IMPLICIT: 'http://rssa_recommender:5000/invoke/implicit_mf',
        LAMBDA_BIASED: 'http://rssa_recommender:5000/invoke/biased_mf',
        LAMBDA_EMOTION: 'http://rssa_recommender:5000/invoke/emotion_mf',
    }

    for _, manifest in REGISTRY.items():
        original_strategy = manifest.strategy
        if isinstance(original_strategy, LambdaStrategy):
            target_url = LOCAL_ROUTE_MAP.get(original_strategy.logical_function_name)

            if target_url:
                manifest.strategy = LocalDevStrategy(
                    local_url=target_url, payload_template=original_strategy.payload_template
                )


def get_registry_keys() -> list[dict[str, str]]:
    """Returns a list of registry keys formatted for frontend selection."""
    return [{'id': key, 'name': key.replace('_', ' ').title()} for key in REGISTRY.keys()]
