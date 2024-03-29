import os
from datetime import datetime, timedelta
from typing import Dict, Tuple, Union, cast
from urllib.parse import urlparse

from aws_lambda_powertools import Logger, Metrics, Tracer  # type: ignore
from aws_lambda_powertools.utilities import parameters

# fixed customer and account id for testing
# and liveliness probe
TEST_CUSTOMER_ID_1 = "CUS_01FWWSK432VY3X1T8A4VNYRTGR"
TEST_ACCOUNT_ID_1 = "ACC_01FWWSNA9DA3N3EQ2JHPQ4WTNR"


def init_monitoring() -> Tuple[Logger, Metrics, Tracer]:
    """initialize logger, metrics and tracer"""
    env = _get_env()
    # default logger service name and level are set by env var in template.yaml
    logger = Logger()
    logger.append_keys(env=env)
    # default metrics namespace and service name are set by env var in template.yaml
    metrics = Metrics()
    metrics.set_default_dimensions(env=env)

    # tracer = Tracer() disable tracer. use new relic instead

    return logger, metrics, None


def get_app_parameters() -> Dict[str, Union[str, int]]:
    env = _get_env()
    try:
        key = f"/vinobank/runtime/vinobank-accounts-api/{env}"
        return cast(Dict[str, Union[str, int]], parameters.get_parameter(key, transform="json"))
    except Exception as e:
        # it's possible that the logger has yet to be initialized
        print(f"cannot retrieve parameter fork key {key}", e)
        return {}


def _get_env() -> str:
    return os.environ.get("DEPLOY_ENV", "feature")


def iso_timestamp(offset: int = 0) -> str:
    """return ISO string of for offset seconds from now"""
    return (datetime.now() + timedelta(seconds=offset)).isoformat()


def is_http_url(url) -> bool:
    try:
        parts = urlparse(url)
        return parts.scheme and parts.scheme in ["http", "https"] and parts.netloc
    except ValueError:
        return False
