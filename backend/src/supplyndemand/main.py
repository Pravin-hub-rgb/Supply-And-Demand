"""Thin ASGI entry point; business logic lives in the package modules."""

from .api import create_app

app = create_app()
