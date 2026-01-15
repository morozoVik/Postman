from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsNotModerator, IsOwner, IsOwnerOrModeratorOrAdmin

from .models import Course, Lesson, Subscription
from .paginators import CoursePagination, LessonPagination
from .serializers import CourseDetailSerializer, CourseSerializer, LessonSerializer
from .tasks import check_and_send_course_updates, send_lesson_update_notifications


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.prefetch_related("lessons").all()
    pagination_class = CoursePagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseSerializer

    def get_permissions(self):
        """Настраиваем права доступа в зависимости от действия"""
        if self.action == "create":
            self.permission_classes = [IsAuthenticated, IsNotModerator]
        elif self.action == "destroy":
            self.permission_classes = [
                IsAuthenticated,
                permissions.IsAdminUser,
            ]
        elif self.action in ["update", "partial_update"]:
            self.permission_classes = [IsAuthenticated, IsOwnerOrModeratorOrAdmin]
        elif self.action in ["list", "retrieve"]:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated]

        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        """Фильтруем queryset в зависимости от прав пользователя"""
        if getattr(self, "swagger_fake_view", False):
            return Course.objects.none()

        user = self.request.user
        if user.is_staff:
            return Course.objects.all()
        if user.groups.filter(name="Модераторы").exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        """При создании курса назначаем текущего пользователя владельцем"""
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """При обновлении курса отправляем уведомления подписчикам"""
        course = serializer.save()

        check_and_send_course_updates.delay(course.id)

        return course

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def send_test_notification(self, request, pk=None):
        """Ручная отправка тестового уведомления для курса"""
        course = self.get_object()

        from .tasks import send_course_update_notifications

        task = send_course_update_notifications.delay(course.id, "обновлен (тест)")

        return Response(
            {
                "status": "Тестовое уведомление отправляется",
                "task_id": task.id,
                "course": course.title,
                "message": f'Тестовое уведомление для курса "{course.title}" поставлено в очередь',
            },
            status=status.HTTP_202_ACCEPTED,
        )


class LessonListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    pagination_class = LessonPagination

    def get_permissions(self):
        """Разные права для списка и создания"""
        if self.request.method == "POST":
            return [IsAuthenticated(), IsNotModerator()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Фильтруем queryset в зависимости от прав пользователя"""
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

        user = self.request.user
        if user.is_staff:
            return Lesson.objects.select_related("course").all()
        if user.groups.filter(name="Модераторы").exists():
            return Lesson.objects.select_related("course").all()
        return Lesson.objects.select_related("course").filter(owner=user)

    def perform_create(self, serializer):
        """При создании урока назначаем текущего пользователя владельцем"""
        lesson = serializer.save(owner=self.request.user)
        send_lesson_update_notifications.delay(lesson.id, "добавлен новый урок")


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Разные права для разных методов"""
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsOwner | permissions.IsAdminUser]
        elif self.request.method in ["PUT", "PATCH"]:
            return [IsAuthenticated(), IsOwnerOrModeratorOrAdmin]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Фильтруем queryset в зависимости от прав пользователя"""
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

        user = self.request.user
        if user.is_staff:
            return Lesson.objects.select_related("course").all()
        if user.groups.filter(name="Модераторы").exists():
            return Lesson.objects.select_related("course").all()
        return Lesson.objects.select_related("course").filter(owner=user)

    def perform_update(self, serializer):
        """При обновлении урока отправляем уведомления"""
        lesson = serializer.save()

        send_lesson_update_notifications.delay(lesson.id, "обновлен урок")

        lesson.course.save()

        check_and_send_course_updates.delay(lesson.course.id)

    def perform_destroy(self, instance):
        """При удалении урока также отправляем уведомления"""
        course = instance.course

        from .tasks import send_course_update_notifications

        send_course_update_notifications.delay(
            course.id, f"обновлен (удален урок: {instance.title})"
        )

        super().perform_destroy(instance)


class SubscriptionAPIView(APIView):
    """APIView для управления подпиской на курс"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get("course_id")

        if not course_id:
            return Response({"error": "course_id обязателен"}, status=400)

        course_item = get_object_or_404(Course, id=course_id)

        subs_exists = Subscription.objects.filter(
            user=user, course=course_item
        ).exists()

        if subs_exists:
            Subscription.objects.filter(user=user, course=course_item).delete()
            message = "Подписка удалена"
            is_subscribed = False
        else:
            Subscription.objects.create(user=user, course=course_item)
            message = "Подписка добавлена"
            is_subscribed = True

        return Response(
            {
                "message": message,
                "course_id": course_id,
                "is_subscribed": is_subscribed,
                "course_title": course_item.title,
            }
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def test_email_view(request):
    """Эндпоинт для тестирования отправки email"""
    from .tasks import test_email_notification

    task = test_email_notification.delay()

    return Response(
        {
            "status": "Тестовая задача отправки email запущена",
            "task_id": task.id,
            "message": "Проверьте логи Celery и вашу почту",
        },
        status=status.HTTP_202_ACCEPTED,
    )
