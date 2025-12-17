from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Payment, User


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


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для CRUD операций с пользователями"""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
            "is_active",
            "is_staff",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "is_active", "is_staff"]


class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
            "phone",
            "city",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def validate_email(self, value):
        """Проверка уникальности email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует"
            )
        return value

    def validate_first_name(self, value):
        """Проверка имени"""
        if not value.strip():
            raise serializers.ValidationError("Имя не может быть пустым")
        return value

    def validate_last_name(self, value):
        """Проверка фамилии"""
        if not value.strip():
            raise serializers.ValidationError("Фамилия не может быть пустой")
        return value

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class UserDetailSerializer(UserSerializer):
    """Расширенный сериализатор для детального просмотра пользователя"""

    payments = PaymentSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["payments"]


class PublicUserSerializer(serializers.ModelSerializer):
    """Сериализатор для публичного просмотра чужого профиля"""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "phone",
            "city",
            "avatar",
            "date_joined",
        ]
        read_only_fields = fields


class PrivateUserSerializer(UserSerializer):
    """Сериализатор для просмотра своего профиля (полная информация)"""

    payments = PaymentSerializer(many=True, read_only=True)
    last_login = serializers.DateTimeField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["payments", "last_login"]
