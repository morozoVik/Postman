from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

from materials.models import Course, Lesson


class UserManager(BaseUserManager):
    """Кастомный менеджер для модели User с email вместо username"""

    def create_user(self, email, password=None, **extra_fields):
        """Создание и сохранение пользователя с email и паролем"""
        if not email:
            raise ValueError("Email обязателен для заполнения")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создание и сохранение суперпользователя"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="Телефон"
    )
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Город")
    avatar = models.ImageField(
        upload_to="users/avatars/", blank=True, null=True, verbose_name="Аватар"
    )
    last_login = models.DateTimeField(
        blank=True, null=True, verbose_name="Последний вход"
    )
    date_joined = models.DateTimeField(
        default=timezone.now, verbose_name="Дата регистрации"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email


class Payment(models.Model):
    PAYMENT_METHOD_CASH = "cash"
    PAYMENT_METHOD_TRANSFER = "transfer"

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_CASH, "Наличные"),
        (PAYMENT_METHOD_TRANSFER, "Перевод на счет"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Пользователь",
    )
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата оплаты")

    paid_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Оплаченный курс",
    )

    paid_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Оплаченный урок",
    )

    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Сумма оплаты"
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="Способ оплаты"
    )

    stripe_product_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID продукта в Stripe"
    )
    stripe_price_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID цены в Stripe"
    )
    stripe_session_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID сессии в Stripe"
    )
    stripe_payment_link = models.URLField(
        max_length=2000, blank=True, null=True, verbose_name="Ссылка на оплату Stripe"
    )
    stripe_payment_status = models.CharField(
        max_length=50,
        default="unpaid",
        verbose_name="Статус оплаты в Stripe",
        choices=[
            ("unpaid", "Не оплачено"),
            ("paid", "Оплачено"),
            ("canceled", "Отменено"),
        ],
    )

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ["-payment_date"]

    def __str__(self):
        if self.paid_course:
            return f"Оплата курса '{self.paid_course.title}' от {self.user.email}"
        elif self.paid_lesson:
            return f"Оплата урока '{self.paid_lesson.title}' от {self.user.email}"
        else:
            return f"Платеж от {self.user.email}"

    def clean(self):
        """Валидация: либо курс, либо урок должен быть заполнен"""
        from django.core.exceptions import ValidationError

        if not self.paid_course and not self.paid_lesson:
            raise ValidationError("Должен быть указан либо курс, либо урок.")
        if self.paid_course and self.paid_lesson:
            raise ValidationError(
                "Можно указать только один из вариантов: курс ИЛИ урок."
            )
