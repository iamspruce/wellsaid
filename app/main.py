from app.core.app import create_app
from app.core.logging import configure_logging

configure_logging()
app = create_app()
