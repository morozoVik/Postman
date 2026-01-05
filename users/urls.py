from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CurrentUserView, PaymentCancelView, PaymentSuccessView,
                    PaymentViewSet, RegisterAPIView, UserViewSet)

router = DefaultRouter()
router.register(r"payments", PaymentViewSet)
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("payments/success/", PaymentSuccessView.as_view(), name="payment-success"),
    path("payments/cancel/", PaymentCancelView.as_view(), name="payment-cancel"),
]
