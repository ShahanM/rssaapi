# in a file like 'core/config.py'
import logging
import os

from config import get_env_var

# def get_env_var(var_name: str, default_value: str = '') -> str:
#     """Helper to get environment variables."""
#     return os.environ.get(var_name, default_value)


AUTH0_DOMAIN = get_env_var('AUTH0_DOMAIN')
AUTH0_API_AUDIENCE = get_env_var('AUTH0_API_AUDIENCE')
AUTH0_ALGORITHMS = [get_env_var('AUTH0_ALGORITHMS', 'RS256')]
AUTH0_ISSUER_URL = f'https://{AUTH0_DOMAIN}/'
AUTH0_JWKS_URL = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'

AUTH0_MANAGEMENT_API_AUDIENCE = get_env_var('AUTH0_MANAGEMENT_API_AUDIENCE')
AUTH0_CLIENT_ID = get_env_var('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = get_env_var('AUTH0_CLIENT_SECRET')
AUTH0_API_ID = get_env_var('AUTH0_API_ID')  # For resource server URL
RESOURCE_SERVER_URL = f'https://{AUTH0_DOMAIN}/api/v2/resource-servers/{AUTH0_API_ID}'

REQUIRED_AUTH0_VARS = [
    AUTH0_DOMAIN,
    AUTH0_API_AUDIENCE,
    AUTH0_MANAGEMENT_API_AUDIENCE,
    AUTH0_CLIENT_ID,
    AUTH0_CLIENT_SECRET,
    AUTH0_API_ID,
]

if any(not var for var in REQUIRED_AUTH0_VARS):
    logging.critical('One or more required Auth0 environment variables are not set.')
