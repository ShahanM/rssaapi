from .strategies import LambdaStrategy

# Assuming these are the names of your deployed Lambda functions
LAMBDA_IMPLICIT = 'ImplicitMFRecsFunction'
LAMBDA_BIASED = 'BiasedMFRecsFunction'
LAMBDA_EMOTION = 'ImplicitMFErsRecsFunction'

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
    'biased_recs_diverse_community_score': LambdaStrategy(
        function_name=LAMBDA_BIASED, payload_template={'path': 'diverse_community_score'}
    ),
    'biased_recs_reference_community_score': LambdaStrategy(
        function_name=LAMBDA_BIASED, payload_template={'path': 'reference_community_score'}
    ),
    # --- Emotion Models ---
    'implicit_ers_top_n': LambdaStrategy(function_name=LAMBDA_EMOTION, payload_template={'path': 'top_n'}),
    'implicit_ers_diverse_n': LambdaStrategy(function_name=LAMBDA_EMOTION, payload_template={'path': 'diverse_n'}),
}


def get_registry_keys() -> list[dict[str, str]]:
    """Returns a list of registry keys formatted for frontend selection."""
    return [{'id': key, 'name': key.replace('_', ' ').title()} for key in REGISTRY.keys()]
