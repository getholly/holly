from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate
from ninja_jwt.authentication import JWTAuth

from holly.holly.api.schemas import ToolSchema
from holly.holly.models.tools import Tools

router = Router(auth=JWTAuth())


@router.get("/", response=list[ToolSchema])
@paginate
def list_tools(request):
    """List Tools.

    Tools is a global, system-managed catalog (populated via the ``populate tools``
    command) and is not user-scoped. Paginated to bound the response size.
    """
    return Tools.objects.all()


@router.get("/{tool_id}", response=ToolSchema)
def get_tool(request, tool_id: int):
    """Get a specific Tool by ID."""
    return get_object_or_404(Tools, id=tool_id)
