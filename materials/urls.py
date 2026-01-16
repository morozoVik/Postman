from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import (
    CourseViewSet,
    LessonListCreateAPIView,
    LessonRetrieveUpdateDestroyAPIView,
    SubscriptionAPIView,
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("lessons/", LessonListCreateAPIView.as_view(), name="lesson-list-create"),
    path(
        "lessons/<int:pk>/",
        LessonRetrieveUpdateDestroyAPIView.as_view(),
        name="lesson-detail",
    ),
    path("subscription/", SubscriptionAPIView.as_view(), name="subscription-manage"),
    path("test-email/", views.test_email_view, name="test-email"),
]
