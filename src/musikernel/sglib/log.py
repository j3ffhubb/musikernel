import logging
import sys


__all__ = [
    'LOG',
]

LOG = logging.getLogger(__name__)
FORMAT = (
    '[%(asctime)s] %(levelname)s %(pathname)-30s: %(lineno)s - %(message)s'
)

def setup_logging(
    format=FORMAT,
    level=logging.INFO,
    log=LOG,
    stream=sys.stdout,
):
    handler = logging.StreamHandler(
        stream=stream,
    )
    fmt = logging.Formatter(format)
    handler.setFormatter(fmt)
    log.addHandler(handler)
    log.setLevel(level)
