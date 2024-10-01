import os
from dotenv import load_dotenv

load_dotenv()

def get_env_var(var_str):
	var = os.getenv(var_str)
	if var is None:
		raise ValueError(f"{var_str} environment variable is not set")
	return var