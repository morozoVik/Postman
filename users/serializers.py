from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    paid_course_title = serializers.CharField(
        source="paid_course.title", read_only=True
    )
    paid_lesson_title = serializers.CharField(
        source="paid_lesson.title", read_only=True
    )
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "user_email",
            "payment_date",
            "paid_course",
            "paid_course_title",
            "paid_lesson",
            "paid_lesson_title",
            "amount",
            "payment_method",
            "payment_method_display",
        ]
        read_only_fields = ["payment_date"]
