from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def healthcheck(request: HttpRequest) -> JsonResponse:
    """Usado pela hospedagem para saber se o app e o banco estão de pé."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})
