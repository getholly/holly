from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate
from ninja_jwt.authentication import JWTAuth

from holly.holly.api.schemas import KnowledgeSchema
from holly.holly.models.knowledge import Knowledge

router = Router(auth=JWTAuth())


@router.get("/", response=list[KnowledgeSchema])
@paginate
def list_knowledge(request):
    """List Knowledge items.

    Knowledge is a global, system-managed catalog (populated via the
    ``populate knowledge`` command) and is not user-scoped, so it is returned to
    every authenticated user. Paginated to bound the response size.
    """
    return Knowledge.objects.all()


@router.get("/{knowledge_id}", response=KnowledgeSchema)
def get_knowledge(request, knowledge_id: int):
    """Get a specific Knowledge item by ID."""
    return get_object_or_404(Knowledge, id=knowledge_id)
