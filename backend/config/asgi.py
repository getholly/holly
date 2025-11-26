"""
ASGI config for holly project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import sys
from pathlib import Path

import uvicorn
from django.core.asgi import get_asgi_application

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "holly"))
APPS_DIR = BASE_DIR / "holly"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

application = get_asgi_application()

if __name__ == "__main__":
    uvicorn.run(
        application, host="127.0.0.1", port=8000, reload=True, log_level="debug", timeout_keep_alive=120, workers=1
    )
