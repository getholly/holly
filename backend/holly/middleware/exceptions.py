import sys

from django.conf import settings
from loguru import logger

DEFAULT_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


def setup_logging(error_log_path: str) -> None:
    logger.remove()

    logger.add(
        sink=error_log_path,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
        serialize=True,
    )

    logger.add(
        sys.stdout,
        level="DEBUG" if settings.DEBUG else "INFO",
        format=DEFAULT_LOG_FORMAT,
        backtrace=True,
        diagnose=True,
    )


class LoguruExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Log detailed exception info with traceback
        logger.opt(exception=True).error(
            f"Exception occurred during request: {request.path}\nMethod: {request.method}\nException: {exception}"
        )
