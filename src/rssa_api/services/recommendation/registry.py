import os

from .strategies import LambdaStrategy

# Assuming these are the names of your deployed Lambda functions
LAMBDA_IMPLICIT = os.environ.get('LAMBDA_NAME_IMPLICIT', 'ImplicitMFRecsFunction')
LAMBDA_BIASED = os.environ.get('LAMBDA_NAME_BIASED', 'BiasedMFRecsFunction')
LAMBDA_EMOTION = os.environ.get('LAMBDA_NAME_EMOTION', 'ImplicitMFErsRecsFunction')

REGISTRY = {
    # --- Implicit Models ---
    'implicit_recs_top_n': LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'top_n'}),
    'implicit_recs_discounted_top_n': LambdaStrategy(
        function_name=LAMBDA_IMPLICIT, payload_template={'path': 'discounted_top_n'}
    ),
    # Additional implicit strategies from rssa-recommender
    'controversial': LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'controversial'}),
    'hate': LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'hate'}),
    'hip': LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'hip'}),
    'no_clue': LambdaStrategy(function_name=LAMBDA_IMPLICIT, payload_template={'path': 'no_clue'}),
    'community_advisors': LambdaStrategy(
        function_name=LAMBDA_IMPLICIT, payload_template={'path': 'community_advisors'}
    ),
    # --- Biased Models ---
    'biased_recs_top_n': LambdaStrategy(function_name=LAMBDA_BIASED, payload_template={'path': 'top_n'}),
    'biased_community_scored': LambdaStrategy(
        function_name=LAMBDA_BIASED, payload_template={'path': 'community_scored_predictions'}
    ),
    'biased_ann_predicted_community_scored': LambdaStrategy(
        function_name=LAMBDA_BIASED,
        payload_template={'path': 'community_scored_predictions', 'ave_score_type': 'nn_predicted'},
    ),
    'biased_ann_observed_community_scored': LambdaStrategy(
        function_name=LAMBDA_BIASED,
        payload_template={'path': 'community_scored_predictions', 'ave_score_type': 'nn_observed'},
    ),
    'biased_global_observed_community_scored': LambdaStrategy(
        function_name=LAMBDA_BIASED,
        payload_template={'path': 'community_scored_predictions', 'ave_score_type': 'global'},
    ),
    # --- Emotion Models ---
    'implicit_ers_top_n': LambdaStrategy(function_name=LAMBDA_EMOTION, payload_template={'path': 'top_n'}),
    'implicit_ers_diverse_n': LambdaStrategy(function_name=LAMBDA_EMOTION, payload_template={'path': 'diverse_n'}),
}


def get_registry_keys() -> list[dict[str, str]]:
    """Returns a list of registry keys formatted for frontend selection."""
    return [{'id': key, 'name': key.replace('_', ' ').title()} for key in REGISTRY.keys()]
