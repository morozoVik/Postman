from rest_framework import serializers

from .models import Course, Lesson, Subscription
from .validators import validate_youtube_url


class LessonSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    date_created = serializers.DateTimeField(read_only=True)
    date_updated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Lesson
        fields = "__all__"
        read_only_fields = ["owner", "date_created", "date_updated"]
        extra_kwargs = {"video_link": {"validators": [validate_youtube_url]}}


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True, source="lessons.all")
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    last_updated = serializers.DateTimeField(read_only=True)
    last_notification_sent = serializers.DateTimeField(read_only=True)
    date_created = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Course
        fields = "__all__"
        read_only_fields = [
            "owner",
            "last_updated",
            "last_notification_sent",
            "date_created",
        ]

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user, course=obj).exists()

        return False


class CourseDetailSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    last_updated = serializers.DateTimeField(read_only=True)
    last_notification_sent = serializers.DateTimeField(read_only=True)
    date_created = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Course
        fields = "__all__"

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user, course=obj).exists()

        return False


class SubscriptionSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = "__all__"
        read_only_fields = ["user", "created_at", "is_active"]
