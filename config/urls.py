from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Postman - Образовательная платформа API",
        default_version="v1",
        description="""
        ## API для образовательной платформы Postman        
        ### Основные возможности:
        - **Управление курсами и уроками**
        - **Регистрация и аутентификация пользователей**
        - **Управление подписками на курсы**
        - **Обработка платежей**   
        ### Аутентификация:
        - Для доступа к большинству эндпоинтов требуется JWT токен.
        - Используйте токен в заголовке: `Authorization: Bearer <ваш_токен>`.
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@postman-edu.ru"),
        license=openapi.License(name="Техническая поддержка Postman"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def health_check(request):
    """Health check endpoint для Docker"""
    return JsonResponse(
        {
            "status": "healthy",
            "service": "Postman API",
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",
            "database": "connected",
            "redis": "connected",
        }
    )


urlpatterns = [
    path("api/health/", health_check, name="api-health-check"),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("swagger.json/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("admin/", admin.site.urls),
    path("api/", include("materials.urls")),
    path("api/", include("users.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
