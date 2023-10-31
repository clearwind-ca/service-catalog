import logging
from tempfile import NamedTemporaryFile

from django.conf import settings

logger = logging.getLogger(__name__)


def dump_webhook(request, slug):
    """
    A temporary debugging tool to dump webhooks out into temparary files.

    So you can then inspect them for testing etc. Should not be in production.
    """
    if settings.DEBUG is False:
        logger.warning("It is not recommended to have DUMP_WEBHOOKS enabled in production")

    file = NamedTemporaryFile(suffix=".txt", mode="w", delete=False)
    logger.info(f"Created {file.name}")

    file.write(f"Slug: {slug}")
    file.write(f"URL: {request.build_absolute_uri()}")
    file.write(f"Method: {request.method}")
    file.write(f"Headers:\n")
    for k, v in request.headers.items():
        file.write(f"  {k}: {v}")
    file.write(f"Body:\n")
    file.write(request.body.decode("utf-8"))

    logger.info(f"Written {file.name}")
