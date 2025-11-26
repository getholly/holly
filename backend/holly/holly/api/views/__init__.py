from ninja import Router
from ninja_jwt.authentication import JWTAuth  # Import JWTAuth

from holly.holly.api.views.caddy import router as caddy_router
from holly.holly.api.views.conversations import router as conversations_router
from holly.holly.api.views.git import router as git_router
from holly.holly.api.views.knowledge import router as knowledge_router
from holly.holly.api.views.llm import router as llm_router
from holly.holly.api.views.mission import router as mission_router
from holly.holly.api.views.notifications import router as notifications_router
from holly.holly.api.views.tools import router as tool_router
from holly.holly.api.views.user_llm_api_key_views import router as llm_keys_router
from holly.holly.api.views.webhooks import router as webhooks_router

router = Router(auth=JWTAuth())  # Apply JWTAuth to all routes in this router
#
# # Include the LLM router
router.add_router("/tools", tool_router, tags=["Tools"])
router.add_router("/llms", llm_router, tags=["LLMs"])
router.add_router("/conversations", conversations_router, tags=["Conversations"])
router.add_router("/knowledge", knowledge_router, tags=["Knowledge"])
router.add_router("/git", git_router, tags=["Git"])
router.add_router("/caddy", caddy_router, tags=["Caddy"])
router.add_router("/missions", mission_router, tags=["Missions"])
router.add_router("/llmkeys", llm_keys_router, tags=["LLM Keys"])
router.add_router("/notifications", notifications_router, tags=["Notifications"])
router.add_router("/webhooks", webhooks_router, tags=["Webhooks"])
