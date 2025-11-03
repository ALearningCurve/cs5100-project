import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).info("logging initialized")

import src.env as _  # noqa
