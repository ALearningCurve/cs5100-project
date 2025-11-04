import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger(__name__).info("logging initialized")

import src.env as _  # noqa
