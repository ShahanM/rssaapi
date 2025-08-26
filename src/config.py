import os
from typing import Union

from dotenv import load_dotenv

load_dotenv()


def get_env_var(var_str: str, default: Union[str, None] = None):
	var = os.getenv(var_str)
	if var is None and default is None:
		raise ValueError(f'{var_str} environment variable is not set')
	elif var is None and default is not None:
		return default
	return var


ROOT_PATH = '/rssa/api/v2'
