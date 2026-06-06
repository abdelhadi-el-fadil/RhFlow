import logging
import sys
from app.config import settings


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("rhflow")


logger = setup_logging()
