import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from materials.models import Course, Lesson
from users.models import Payment

User = get_user_model()


class Command(BaseCommand):
    help = "Создает тестовые платежи"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=10, help="Количество создаваемых платежей"
        )

    def handle(self, *args, **options):
        count = options["count"]

        self.stdout.write("Создание тестовых платежей...")

        user1, created = User.objects.get_or_create(
            email="user1@example.com",
            defaults={"first_name": "Иван", "last_name": "Иванов", "is_active": True},
        )
        if created:
            user1.set_password("12345")
            user1.save()
            self.stdout.write(f"Создан пользователь: {user1.email}")

        user2, created = User.objects.get_or_create(
            email="user2@example.com",
            defaults={"first_name": "Мария", "last_name": "Петрова", "is_active": True},
        )
        if created:
            user2.set_password("12345")
            user2.save()
            self.stdout.write(f"Создан пользователь: {user2.email}")

        courses = list(Course.objects.all())
        lessons = list(Lesson.objects.all())

        if not courses:
            self.stdout.write("Создаю тестовые курсы...")
            course1 = Course.objects.create(
                title="Python для начинающих", description="Изучение основ Python"
            )
            course2 = Course.objects.create(
                title="Django разработка",
                description="Создание веб-приложений на Django",
            )
            courses = [course1, course2]

        if not lessons:
            self.stdout.write("Создаю тестовые уроки...")
            lesson1 = Lesson.objects.create(
                title="Введение в Python",
                description="Первые шаги в Python",
                course=courses[0],
            )
            lesson2 = Lesson.objects.create(
                title="Установка Django",
                description="Настройка окружения",
                course=courses[1],
            )
            lessons = [lesson1, lesson2]

        payment_methods = ["cash", "transfer"]

        payments_created = 0
        for i in range(count):
            if random.choice([True, False]):
                paid_course = random.choice(courses)
                paid_lesson = None
                amount = Decimal(str(random.randint(10000, 50000) / 100))
            else:
                paid_course = None
                paid_lesson = random.choice(lessons)
                amount = Decimal(str(random.randint(1000, 10000) / 100))

            user = random.choice([user1, user2])

            payment_date = datetime.now() - timedelta(days=random.randint(0, 30))

            payment = Payment.objects.create(
                user=user,
                paid_course=paid_course,
                paid_lesson=paid_lesson,
                amount=amount,
                payment_method=random.choice(payment_methods),
                payment_date=payment_date,
            )

            payments_created += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ Успешно создано {payments_created} платежей")
        )
