"""
User API package - FastAPI REST endpoints with cache integration.
"""

__version__ = "0.1.0"

from .main import app
from .models import User, UserInternal
from .dal import UserDAL
from .api import router

__all__ = [
    "app",
    "User",
    "UserInternal",
    "UserDAL",
    "router",
]
