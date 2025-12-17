from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from materials.models import Course, Lesson
from materials.serializers import LessonSerializer
from materials.validators import validate_youtube_url

User = get_user_model()


class YouTubeURLValidatorTestCase(TestCase):
    """
    Базовые тесты для валидатора YouTube ссылок
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        self.course = Course.objects.create(
            title="Тестовый курс",
            description="Описание тестового курса",
            owner=self.user,
        )

    def test_valid_youtube_urls(self):
        """Тестирование корректных YouTube ссылок"""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://youtube.com/embed/dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtu.be/dQw4w9WgXcQ",
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                try:
                    validate_youtube_url(url)
                except ValidationError:
                    self.fail(
                        f"Валидатор не должен выбрасывать исключение для валидного URL: {url}"
                    )

    def test_invalid_youtube_urls(self):
        """Тестирование некорректных YouTube ссылок"""
        invalid_urls = [
            "https://vimeo.com/123456789",
            "https://example.com/video",
            "ftp://youtube.com/watch?v=123",
            "youtube.com/watch?v=123",
            "www.youtube.com",
            "https://fakeyoutube.com/video",
            "https://youtube.fake.com/video",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValidationError):
                    validate_youtube_url(url)

    def test_empty_url(self):
        """Тестирование пустой ссылки"""
        try:
            validate_youtube_url("")
            validate_youtube_url(None)
        except ValidationError:
            self.fail("Валидатор не должен выбрасывать исключение для пустой ссылки")

    def test_malformed_url(self):
        """Тестирование некорректного формата URL"""
        with self.assertRaises(ValidationError):
            validate_youtube_url("not-a-url")

    def test_lesson_with_valid_url(self):
        """Создание урока с валидной YouTube ссылкой"""
        lesson = Lesson(
            title="Тестовый урок",
            description="Описание тестового урока",
            course=self.course,
            video_link="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            owner=self.user,
        )

        lesson.full_clean()
        lesson.save()

        self.assertEqual(Lesson.objects.count(), 1)
        self.assertEqual(Lesson.objects.first().title, "Тестовый урок")

    def test_lesson_with_invalid_url(self):
        """Создание урока с невалидной ссылкой"""
        lesson = Lesson(
            title="Невалидный урок",
            description="Описание",
            course=self.course,
            video_link="https://vimeo.com/123456789",  # Не YouTube!
            owner=self.user,
        )

        with self.assertRaises(ValidationError):
            lesson.full_clean()


class LessonSerializerTestCase(TestCase):
    """
    Тесты для сериализатора уроков
    """

    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email="serializer@example.com", password="testpass123"
        )

        self.course = Course.objects.create(
            title="Курс для тестов", description="Описание", owner=self.user
        )

    def test_serializer_valid_url(self):
        """Тестирование сериализатора с валидной YouTube ссылкой"""
        data = {
            "title": "Урок с YouTube",
            "description": "Описание урока",
            "course": self.course.id,
            "video_link": "https://www.youtube.com/watch?v=abc123",
        }

        serializer = LessonSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_invalid_url(self):
        """Тестирование сериализатора с невалидной ссылкой"""
        data = {
            "title": "Урок с невалидной ссылкой",
            "description": "Описание",
            "course": self.course.id,
            "video_link": "https://vimeo.com/123456789",
        }

        serializer = LessonSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("video_link", serializer.errors)

    def test_serializer_update_url(self):
        """Обновление ссылки в уроке"""
        # Создаем урок
        lesson = Lesson.objects.create(
            title="Старый урок",
            description="Описание",
            course=self.course,
            video_link="https://www.youtube.com/watch?v=old123",
            owner=self.user,
        )

        data = {"video_link": "https://youtu.be/new123"}

        serializer = LessonSerializer(lesson, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_lesson = serializer.save()

        self.assertEqual(updated_lesson.video_link, "https://youtu.be/new123")

    def test_serializer_create_lesson(self):
        """Создание урока через сериализатор"""
        data = {
            "title": "Новый урок через сериализатор",
            "description": "Описание нового урока",
            "course": self.course.id,
            "video_link": "https://www.youtube.com/embed/xyz789",
        }

        serializer = LessonSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        lesson = serializer.save(owner=self.user)
        self.assertEqual(lesson.title, "Новый урок через сериализатор")
        self.assertEqual(lesson.video_link, "https://www.youtube.com/embed/xyz789")
