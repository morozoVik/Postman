from django.db.models import Prefetch
from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Course, Lesson
from .serializers import (CourseDetailSerializer, CourseSerializer,
                          LessonSerializer)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.prefetch_related("lessons").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseSerializer


class LessonListCreateAPIView(generics.ListCreateAPIView):
    queryset = Lesson.objects.select_related("course").all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.select_related("course").all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
