import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv


def find_project_root() -> Path:
    """Finds the project root directory by searching upward for pyproject.toml."""
    # Start the search from the directory of the current file
    current_dir = Path(__file__).resolve().parent

    # Walk up the directory tree
    for parent in current_dir.parents:
        if (parent / 'pyproject.toml').exists():
            return parent

    # Fallback if the file is not found (or for debugging)
    raise RuntimeError('Could not find pyproject.toml in the current or parent directories.')


try:
    PROJECT_ROOT = find_project_root()
except RuntimeError as e:
    # Handle the case where root isn't found during import time
    print(f'CRITICAL PATH ERROR: {e}', file=sys.stderr)
    # Define a blank path so imports don't crash, but functions that use it will fail later
    PROJECT_ROOT = Path('/')

# Define key absolute paths based on the root
# Runtime Directories
RUNTIME_DIR = PROJECT_ROOT / 'runtime'
LOGS_DIR = RUNTIME_DIR / 'logs'
CACHE_DIR = RUNTIME_DIR / 'cache'

# Asset Directories (Static Files)
ASSETS_DIR = PROJECT_ROOT / 'assets'
MODELS_DIR = ASSETS_DIR / 'models'

# Ensure runtime directories exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)


load_dotenv()


def get_env_var(var_name: str, default_value: str = '') -> str:
    """Helper to get environment variables."""
    return os.environ.get(var_name, default_value)


ROOT_PATH = '/rssa/api'


def configure_logging():
    # Assuming LOGS_DIR is imported correctly from core.config
    # Example: from core.config import LOGS_DIR

    # --- 1. Define Paths and Constants ---

    # Calculate the date-stamped file name string explicitly
    log_file_name = time.strftime('%Y%m%d_%H%M%S.log')
    LOG_FILE_PATH = LOGS_DIR / log_file_name

    LOG_LEVEL = logging.INFO  # Set the minimum level to capture
    LOG_FORMAT_FILE = '%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    LOG_FORMAT_CONSOLE = '%(levelname)s: %(message)s'  # Simpler format for console

    # Ensure log directory exists (if it wasn't done in config.py)
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # --- 2. Configure the Root Logger ---

    # Basic config sets up the FILE handler and the root logger level.
    # We pass the Path object converted to a string using .as_posix()
    logging.basicConfig(filename=LOG_FILE_PATH.as_posix(), level=LOG_LEVEL, format=LOG_FORMAT_FILE)

    # --- 3. Add Console Handler (StreamHandler) ---

    # We get the root logger instance
    root_logger = logging.getLogger()

    # Console Handler: Always output to terminal (stderr by default)
    console_handler = logging.StreamHandler()

    # We want INFO or higher to the file, but let's set console to WARNING/ERROR
    # to keep the terminal clean unless important things happen.
    console_handler.setLevel(logging.INFO)

    # Apply a different, cleaner format for the console
    console_formatter = logging.Formatter(LOG_FORMAT_CONSOLE)
    console_handler.setFormatter(console_formatter)

    # Add the console handler to the root logger
    root_logger.addHandler(console_handler)

    # Optional: Suppress noisy logging from third-party libraries (like HTTPX/SQLAlchemy)
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


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
