import logging

import uvicorn
from fastapi import FastAPI
from gradio.routes import App as App

from src.app.auth import router as auth_router
from src.app.chatapp import mount_chat_interface
from src.app.rate_limit import mount as mount_rate_limiter

logger = logging.getLogger(__name__)


def launch(run: bool = True) -> FastAPI:
  """Runs and launches the app."""
  app = FastAPI()

  # add middleware
  mount_rate_limiter(app)

  # add routes
  app.include_router(auth_router)
  app = mount_chat_interface(app)

  if run:
    uvicorn.run(app, host="0.0.0.0", port=8080)

  return app
