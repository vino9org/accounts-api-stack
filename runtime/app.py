from typing import Any, Dict

from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from accounts_api import handle_event, utils

logger, metrics, tracer = utils.init_monitoring()


def lambda_handler(event: Dict[str, Any], context: LambdaContext):
    logger.info(event)
    eb_event = EventBridgeEvent(event)
    return handle_event(eb_event.detail)
