import os
from pathlib import Path


def must_str(env_var: str) -> str:
    value = os.environ.get(env_var)
    if value is None:
        raise ValueError(f'missing required environment variable {env_var}')
    return value


def must_path(env_var: str) -> Path:
    return Path(must_str(env_var)).absolute()


def must_list(env_var: str) -> list[str]:
    return must_str(env_var).split(' ')
