import os

from dotenv import load_dotenv

load_dotenv()


def get_env_var(var_name: str, default_value: str = '') -> str:
    """Helper to get environment variables."""
    return os.environ.get(var_name, default_value)


ROOT_PATH = '/rssa/api'
