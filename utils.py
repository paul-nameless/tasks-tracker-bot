import logging
import logging.handlers
import json

logger = logging.getLogger(__name__)


def init_log():
    handlers = [logging.StreamHandler()]

    # capture warnings, along with asyncio runtime warnings
    # e.g. RuntimeWaring: coroutine <X> was never awaited
    logging.captureWarnings(True)

    logging.basicConfig(
        format='%(levelname)-8s [%(asctime)s] %(message).1000s',
        level=logging.DEBUG,
        handlers=handlers,
    )


def encode(msg):
    return json.dumps(msg).encode()


def decode(msg):
    return json.loads(msg.decode())
