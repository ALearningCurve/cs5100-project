from typing import Annotated

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from src.app.rate_limit import limiter
from src.env import (
  AUTHENTICATION_SECRET_KEY,
  AUTHENTICATION_USERNAME,
  SHOULD_AUTHENTICATE,
)

SKIP_AUTHENTICATION = not SHOULD_AUTHENTICATE
AUTH_COOKIE_NAME = "chat_access_token"
COOKIE_LIFESPAN_DAYS = 180

router = APIRouter()


def get_authenticated_user(request: Request) -> str | None:
  """Check if the user has the valid secret key in their cookies."""
  valid = (
    SKIP_AUTHENTICATION
    or request.cookies.get(AUTH_COOKIE_NAME) == AUTHENTICATION_SECRET_KEY
  )

  return "admin" if valid else None


@router.get("/")
async def index(request: Request) -> RedirectResponse:
  """Redirect to chat if authed, otherwise show login."""
  if get_authenticated_user(request):
    return RedirectResponse(url="/chat")
  return RedirectResponse(url="/login")


@router.get("/health")
@limiter.exempt
async def health(request: Request) -> Response:
  """Show health status."""
  return HTMLResponse("<h1>OK<h1/>")


@router.get("/login")
async def login_page(request: Request) -> Response:
  """A simple HTML login form."""
  if get_authenticated_user(request):
    # if already authed, punt back to the chatapp
    return RedirectResponse(url="/chat")

  # show login form for the user
  return HTMLResponse("""
    <html>
        <body style="font-family: sans-serif; display: flex; justify-content: center; padding-top: 50px;">
            <form action="/login" method="post" style="border: 1px solid #ccc; padding: 20px; border-radius: 8px;">
                <h2>Username</h2>
                <input type="text" name="username" placeholder="Username..." required style="padding: 8px;"><br><br>
                <h2>Password</h2>
                <input type="password" name="password" placeholder="Password..." required style="padding: 8px;"><br><br>
                <button type="submit" style="padding: 8px 16px; cursor: pointer;">Access App</button>
            </form>
        </body>
    </html>
    """)  # noqa: E501


class UserLogin(BaseModel):
  """Represents DTO for user login."""

  username: str
  password: str


@router.post("/login")
@limiter.limit("10/minute")
async def do_login(
  user_data: Annotated[UserLogin, Form()], request: Request
) -> Response:
  """Verify key and set the cookie."""
  goto_chat_response = RedirectResponse(url="/chat", status_code=303)
  if SKIP_AUTHENTICATION:
    return goto_chat_response

  assert AUTHENTICATION_SECRET_KEY is not None

  if (
    user_data.password == AUTHENTICATION_SECRET_KEY
    and user_data.username == AUTHENTICATION_USERNAME
  ):
    response = RedirectResponse(url="/chat", status_code=303)
    response.set_cookie(
      key=AUTH_COOKIE_NAME,
      value=AUTHENTICATION_SECRET_KEY,
      max_age=COOKIE_LIFESPAN_DAYS * 24 * 60 * 60,
      httponly=True,
      samesite="strict",
    )
    return response
  return HTMLResponse("Incorrect Key. <a href='/login'>Try again</a>", status_code=401)
