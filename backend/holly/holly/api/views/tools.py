from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from holly.holly.api.schemas import ToolSchema
from holly.holly.models.tools import Tools

router = Router(auth=JWTAuth())


@router.get("/", response=list[ToolSchema])
def list_tools(request):
    """List all Tools."""
    return Tools.objects.all()


@router.get("/{tool_id}", response=ToolSchema)
def get_tool(request, tool_id: int):
    """Get a specific Tool by ID."""
    return get_object_or_404(Tools, id=tool_id)
