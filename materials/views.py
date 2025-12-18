from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import (CanViewOwnObjects, IsAdminOrModerator,
                               IsModerator, IsNotModerator, IsOwner,
                               IsOwnerOrModeratorOrAdmin)

from .models import Course, Lesson, Subscription
from .paginators import CoursePagination, LessonPagination
from .serializers import (CourseDetailSerializer, CourseSerializer,
                          LessonSerializer, SubscriptionSerializer)


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
                IsOwner | permissions.IsAdminUser,
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
        user = self.request.user
        if user.is_staff:
            return Course.objects.all()
        if user.groups.filter(name="Модераторы").exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        """При создании курса назначаем текущего пользователя владельцем"""
        serializer.save(owner=self.request.user)


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
        user = self.request.user
        if user.is_staff:
            return Lesson.objects.select_related("course").all()
        if user.groups.filter(name="Модераторы").exists():
            return Lesson.objects.select_related("course").all()
        return Lesson.objects.select_related("course").filter(owner=user)

    def perform_create(self, serializer):
        """При создании урока назначаем текущего пользователя владельцем"""
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer

    def get_permissions(self):
        """Разные права для разных методов"""
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsOwner | permissions.IsAdminUser]
        elif self.request.method in ["PUT", "PATCH"]:
            return [IsAuthenticated(), IsOwnerOrModeratorOrAdmin]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Фильтруем queryset в зависимости от прав пользователя"""
        user = self.request.user
        if user.is_staff:
            return Lesson.objects.select_related("course").all()
        if user.groups.filter(name="Модераторы").exists():
            return Lesson.objects.select_related("course").all()
        return Lesson.objects.select_related("course").filter(owner=user)


class SubscriptionAPIView(APIView):
    """APIView для управления подпиской на курс"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response({"error": "course_id обязателен"}, status=400)

        course_item = get_object_or_404(Course, id=course_id)

        subs_exists = Subscription.objects.filter(user=user, course=course_item).exists()

        if subs_exists:
            Subscription.objects.filter(user=user, course=course_item).delete()
            message = 'Подписка удалена'
            is_subscribed = False
        else:
            Subscription.objects.create(user=user, course=course_item)
            message = 'Подписка добавлена'
            is_subscribed = True

        return Response({"message": message, "course_id": course_id, "is_subscribed": is_subscribed, "course_title": course_item.title})
