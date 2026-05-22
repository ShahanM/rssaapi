import os
from dataclasses import dataclass

from .strategies import LambdaStrategy

LAMBDA_IMPLICIT = os.environ.get('LAMBDA_NAME_IMPLICIT', 'ImplicitMFRecsFunction')
LAMBDA_BIASED = os.environ.get('LAMBDA_NAME_BIASED', 'BiasedMFRecsFunction')
LAMBDA_EMOTION = os.environ.get('LAMBDA_NAME_IMPLICIT_ERS', 'ImplicitMFErsRecsFunction')


@dataclass
class StrategyManifest:
    """Defines the capabilities and boundaries of a recommendation algorithm."""

    strategy: LambdaStrategy
    domain: str
    id_field: str
    default_schema: str
    supported_schemas: set[str]


REGISTRY: dict[str, StrategyManifest] = {
    # --- Implicit Models ---
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
    'community_advisors': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'community_advisors'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='advisor',
        supported_schemas={'community_advisors'},
    ),
    # --- Biased Models ---
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
    # --- Emotion Models ---
    'implicit_ers_top_n': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_EMOTION, payload_template={'path': 'top_n'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard_emotion',
        # The Emotion model can serve it all!
        supported_schemas={'standard_emotion'},
    ),
    'implicit_ers_diverse_n': StrategyManifest(
        strategy=LambdaStrategy(function_name=LAMBDA_EMOTION, payload_template={'path': 'diverse_n'}),
        domain='movies',
        id_field='movielens_id',
        default_schema='standard_emotion',
        supported_schemas={'standard_emotion'},
    ),
}


def get_registry_keys() -> list[dict[str, str]]:
    """Returns a list of registry keys formatted for frontend selection."""
    return [{'id': key, 'name': key.replace('_', ' ').title()} for key in REGISTRY.keys()]


# REGISTRY: dict[str, StrategyManifest] = {
#     # --- Implicit Models ---
#     'implicit_recs_top_n': LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'top_n'}),
#     'implicit_recs_discounted_top_n': LambdaStrategy(
#         function_name=LAMBDA_IMPLICIT, payload_template={'path': 'discounted_top_n'}
#     ),
#     # Additional implicit strategies from rssa-recommender
#     'controversial': LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'controversial'}),
#     'hate': LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'hate'}),
#     'hip': LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'hip'}),
#     'no_clue': LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'no_clue'}),
#     'community_advisors': LambdaStrategy(
#         function_name=LAMBDA_IMPLICIT, payload_template={'path': 'community_advisors'}
#     ),
#     # --- Biased Models ---
#     'biased_recs_top_n': LambdaStrategy(function_name=LAMBDA_BIASED, payload_template={'path': 'top_n'}),
#     'biased_community_scored': LambdaStrategy(
#         function_name=LAMBDA_BIASED, payload_template={'path': 'community_scored_predictions'}
#     ),
#     'biased_ann_predicted_community_scored': LambdaStrategy(
#         function_name=LAMBDA_BIASED,
#         payload_template={'path': 'community_scored_predictions', 'ave_score_type': 'nn_predicted'},
#     ),
#     'biased_ann_observed_community_scored': LambdaStrategy(
#         function_name=LAMBDA_BIASED,
#         payload_template={'path': 'community_scored_predictions', 'ave_score_type': 'nn_observed'},
#     ),
#     'biased_global_observed_community_scored': LambdaStrategy(
#         function_name=LAMBDA_BIASED,
#         payload_template={'path': 'community_scored_predictions', 'ave_score_type': 'global'},
#     ),
#     # --- Emotion Models ---
#     'implicit_ers_top_n': LambdaStrategy(function_name=LAMBDA_EMOTION, payload_template={'path': 'top_n'}),
#     'implicit_ers_diverse_n': LambdaStrategy(function_name=LAMBDA_EMOTION, payload_template={'path': 'diverse_n'}),
# }


# def get_registry_keys() -> list[dict[str, str]]:
#     """Returns a list of registry keys formatted for frontend selection."""
#     return [{'id': key, 'name': key.replace('_', ' ').title()} for key in REGISTRY.keys()]
