from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, User
from .paginators import PaymentPagination, UserPagination
from .permissions import IsOwnerOrModeratorOrAdmin
from .serializers import (
    PaymentSerializer,
    PrivateUserSerializer,
    PublicUserSerializer,
    UserDetailSerializer,
    UserRegisterSerializer,
    UserSerializer,
)


class RegisterAPIView(generics.CreateAPIView):
    """API для регистрации пользователя (публичный)"""

    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pagination_class = UserPagination

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия и прав"""
        if self.action == "create":
            return UserRegisterSerializer
        elif self.action == "retrieve":
            if self.request.user.id == int(self.kwargs.get("pk", 0)):
                return PrivateUserSerializer
            else:
                return PublicUserSerializer
        return UserSerializer

    def get_permissions(self):
        """Настраиваем права доступа"""
        if self.action == "create":
            return [permissions.AllowAny()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), permissions.IsOwner]
        else:
            return [IsAuthenticated()]

    def get_queryset(self):
        """Фильтруем пользователей в зависимости от прав"""
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        if user.groups.filter(name="Модераторы").exists():
            return User.objects.all()
        return User.objects.all()

    def update(self, request, *args, **kwargs):
        """Ограничиваем обновление только своего профиля"""
        instance = self.get_object()
        if instance != request.user:
            return Response(
                {"detail": "Вы можете редактировать только свой профиль."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Ограничиваем частичное обновление только своего профиля"""
        instance = self.get_object()
        if instance != request.user:
            return Response(
                {"detail": "Вы можете редактировать только свой профиль."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Ограничиваем удаление только своего профиля"""
        instance = self.get_object()
        if instance != request.user and not request.user.is_staff:
            return Response(
                {"detail": "Вы можете удалить только свой профиль."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PaymentPagination

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["payment_method", "paid_course", "paid_lesson"]
    ordering_fields = ["payment_date", "amount"]
    ordering = ["-payment_date"]

    def get_queryset(self):
        """Фильтруем платежи в зависимости от прав пользователя"""
        user = self.request.user

        if user.is_staff:
            return Payment.objects.all()
        if user.groups.filter(name="Модераторы").exists():
            return Payment.objects.all()
        return Payment.objects.filter(user=user)


class CurrentUserView(APIView):
    """API для получения текущего пользователя"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Всегда возвращаем полную информацию о текущем пользователе"""
        serializer = PrivateUserSerializer(request.user)
        return Response(serializer.data)
