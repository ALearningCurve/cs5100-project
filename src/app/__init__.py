import logging

import uvicorn
from fastapi import FastAPI
from gradio.routes import App as App

from src.app.auth import router as auth_router
from src.app.chatapp import mount_chat_interface

logger = logging.getLogger(__name__)


def launch() -> None:
  """Runs and launches the app."""
  app = FastAPI()
  app.include_router(auth_router)
  app = mount_chat_interface(app)

  uvicorn.run(app, host="0.0.0.0", port=8000)
