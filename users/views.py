from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
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
from .services import (
    create_stripe_checkout_session,
    create_stripe_price,
    create_stripe_product,
    retrieve_stripe_session,
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
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()

        user = self.request.user

        if user.is_staff:
            return Payment.objects.all()
        if user.groups.filter(name="Модераторы").exists():
            return Payment.objects.all()
        return Payment.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        """Создание платежа с интеграцией Stripe"""
        paid_course = request.data.get("paid_course")
        paid_lesson = request.data.get("paid_lesson")

        if not paid_course and not paid_lesson:
            return Response(
                {"detail": "Должен быть указан либо курс, либо урок."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if paid_course and paid_lesson:
            return Response(
                {"detail": "Можно указать только один из вариантов: курс ИЛИ урок."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            if paid_course:
                from materials.models import Course

                course = Course.objects.get(id=paid_course)
                product_name = f"Курс: {course.title}"
                product_description = (
                    course.description or f"Оплата курса {course.title}"
                )
            else:
                from materials.models import Lesson

                lesson = Lesson.objects.get(id=paid_lesson)
                product_name = f"Урок: {lesson.title}"
                product_description = f"Оплата урока {lesson.title}"

            amount = serializer.validated_data.get("amount")

            stripe_product_id = create_stripe_product(
                name=product_name, description=product_description
            )

            stripe_price_id = create_stripe_price(
                product_id=stripe_product_id, amount=amount
            )

            metadata = {
                "user_id": request.user.id,
                "payment_type": "course" if paid_course else "lesson",
                "course_id": paid_course or "",
                "lesson_id": paid_lesson or "",
            }

            from django.conf import settings

            session_data = create_stripe_checkout_session(
                price_id=stripe_price_id,
                success_url=settings.FRONTEND_SUCCESS_URL,
                cancel_url=settings.FRONTEND_CANCEL_URL,
                metadata=metadata,
            )

            payment_data = serializer.validated_data
            payment_data.update(
                {
                    "user": request.user,
                    "stripe_product_id": stripe_product_id,
                    "stripe_price_id": stripe_price_id,
                    "stripe_session_id": session_data["session_id"],
                    "stripe_payment_link": session_data["payment_link"],
                    "stripe_payment_status": session_data["payment_status"],
                }
            )

            payment = Payment.objects.create(**payment_data)

            response_serializer = self.get_serializer(payment)
            headers = self.get_success_headers(response_serializer.data)

            return Response(
                {
                    **response_serializer.data,
                    "payment_link": session_data["payment_link"],
                },
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        except Exception as e:
            return Response(
                {"detail": f"Ошибка при создании платежа: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        """Проверка статуса платежа в Stripe"""
        payment = self.get_object()

        if payment.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "У вас нет прав для просмотра этого платежа."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not payment.stripe_session_id:
            return Response(
                {"detail": "Этот платеж не создан через Stripe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session_info = retrieve_stripe_session(payment.stripe_session_id)

            payment.stripe_payment_status = session_info["payment_status"]
            payment.save()

            return Response(
                {
                    "payment_id": payment.id,
                    "stripe_session_id": payment.stripe_session_id,
                    "payment_status": payment.stripe_payment_status,
                    "amount_total": session_info.get("amount_total"),
                    "currency": session_info.get("currency"),
                    "customer_details": session_info.get("customer_details"),
                }
            )
        except Exception as e:
            return Response(
                {"detail": f"Ошибка при получении статуса: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CurrentUserView(APIView):
    """API для получения текущего пользователя"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Всегда возвращаем полную информацию о текущем пользователе"""
        serializer = PrivateUserSerializer(request.user)
        return Response(serializer.data)


class PaymentSuccessView(APIView):
    """Вьюшка для успешного редиректа после оплаты"""

    permission_classes = []

    def get(self, request):

        return HttpResponse("Оплата успешно завершена! Спасибо за покупку.")


class PaymentCancelView(APIView):
    """Вьюшка для отмены оплаты"""

    permission_classes = []

    def get(self, request):
        return HttpResponse("Оплата отменена. Вы можете попробовать снова.")
