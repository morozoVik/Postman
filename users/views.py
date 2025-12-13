from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, User
from .serializers import (PaymentSerializer, UserDetailSerializer,
                          UserRegisterSerializer, UserSerializer)


class RegisterAPIView(generics.CreateAPIView):
    """API для регистрации пользователя (публичный)"""

    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для CRUD операций с пользователями"""

    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegisterSerializer
        elif self.action == "retrieve":
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        """Разрешения: регистрация - публичная, остальное - только для авторизованных"""
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Обычные пользователи видят только себя, администраторы - всех"""
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]

    filterset_fields = ["payment_method", "paid_course", "paid_lesson"]

    ordering_fields = ["payment_date", "amount"]
    ordering = ["-payment_date"]

    def get_queryset(self):
        """Пользователи видят только свои платежи"""
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=user)


class CurrentUserView(APIView):
    """API для получения текущего пользователя"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
