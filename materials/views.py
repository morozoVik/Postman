from django.db.models import Prefetch
from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsAdminOrModerator, IsModerator, IsOwner

from .models import Course, Lesson
from .serializers import CourseDetailSerializer, CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.prefetch_related("lessons").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseSerializer

    def get_permissions(self):
        """Настраиваем права доступа в зависимости от действия"""
        if self.action == "create":
            self.permission_classes = [IsAuthenticated]
        elif self.action == "destroy":
            self.permission_classes = [
                IsAuthenticated,
                IsOwner | permissions.IsAdminUser,
            ]
        elif self.action in ["update", "partial_update"]:
            self.permission_classes = [IsAuthenticated, IsOwner | IsAdminOrModerator]
        else:
            self.permission_classes = [IsAuthenticated]

        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        """При создании курса назначаем текущего пользователя владельцем"""
        serializer.save(owner=self.request.user)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    queryset = Lesson.objects.select_related("course").all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Разные права для списка и создания"""
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """При создании урока назначаем текущего пользователя владельцем"""
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.select_related("course").all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Разные права для разных методов"""
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsOwner | permissions.IsAdminUser]
        elif self.request.method in ["PUT", "PATCH"]:
            return [IsAuthenticated(), IsOwner | IsAdminOrModerator]
        return [IsAuthenticated()]
