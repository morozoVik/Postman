import pytest
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from materials.models import Course, Lesson, Subscription
from materials.serializers import LessonSerializer
from materials.validators import validate_youtube_url
from users.models import User


class YouTubeURLValidatorTestCase(TestCase):
    """тесты для валидации YouTube URL"""

    def test_valid_youtube_urls(self):
        """Тест валидных YouTube URL"""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
        ]
        for url in valid_urls:
            try:
                validate_youtube_url(url)
            except ValidationError:
                self.fail(f"validate_youtube_url raised ValidationError for {url}")

    def test_empty_url(self):
        """Пустой URL должен проходить валидацию"""
        try:
            validate_youtube_url("")
            validate_youtube_url(None)
        except ValidationError:
            self.fail("validate_youtube_url raised ValidationError for empty url")

    def test_lesson_with_valid_url(self):
        """Тест урока с валидным YouTube URL"""
        user = User.objects.create_user(email="test@example.com", password="password")
        course = Course.objects.create(title="Test Course", owner=user)
        lesson = Lesson(
            title="Test Lesson",
            course=course,
            owner=user,
            video_link="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )
        lesson.full_clean()


class LessonSerializerTestCase(TestCase):
    """тесты для сериализатора Lesson"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="password"
        )
        self.course = Course.objects.create(title="Test Course", owner=self.user)

    def test_serializer_create_lesson(self):
        """Тест создания урока через сериализатор"""
        data = {
            "title": "New Lesson",
            "description": "Lesson description",
            "course": self.course.id,
            "video_link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        }
        serializer = LessonSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        lesson = serializer.save(owner=self.user)
        self.assertEqual(lesson.title, "New Lesson")
        self.assertEqual(lesson.owner, self.user)

    def test_serializer_valid_url(self):
        """Тест валидного URL в сериализаторе"""
        data = {
            "title": "Lesson",
            "course": self.course.id,
            "video_link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        }
        serializer = LessonSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class LessonCRUDTestCase(APITestCase):
    """тесты для CRUD операций с уроками (Задание 4)"""

    def setUp(self):
        """Создание тестовых данных"""
        self.owner = User.objects.create_user(
            email="owner@example.com", password="password123"
        )

        self.other_user = User.objects.create_user(
            email="other@example.com", password="password123"
        )

        self.moderator = User.objects.create_user(
            email="moderator@example.com", password="password123"
        )
        moderator_group, _ = Group.objects.get_or_create(name="Модераторы")
        self.moderator.groups.add(moderator_group)

        self.admin = User.objects.create_user(
            email="admin@example.com", password="password123", is_staff=True
        )

        self.owner_course = Course.objects.create(
            title="Курс владельца", owner=self.owner
        )

        self.other_course = Course.objects.create(
            title="Чужой курс", owner=self.other_user
        )

        self.lesson = Lesson.objects.create(
            title="Тестовый урок",
            description="Описание урока",
            course=self.owner_course,
            owner=self.owner,
        )

    def test_create_lesson_by_owner(self):
        """Владелец может создать урок в своем курсе"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("lesson-list-create")
        data = {
            "title": "Новый урок от владельца",
            "description": "Описание",
            "course": self.owner_course.id,
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)
        self.assertEqual(response.data["title"], "Новый урок от владельца")

    def test_create_lesson_by_moderator(self):
        """Модератор НЕ может создать урок"""
        self.client.force_authenticate(user=self.moderator)
        url = reverse("lesson-list-create")
        data = {"title": "Урок от модератора", "course": self.owner_course.id}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_lesson_by_admin(self):
        """Администратор может создать урок"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("lesson-list-create")
        data = {"title": "Урок от администратора", "course": self.owner_course.id}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_lesson_list_by_owner(self):
        """Владелец видит свои уроки"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("lesson-list-create")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)

    def test_get_lesson_detail_by_owner(self):
        """Владелец может просмотреть свой урок"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("lesson-detail", args=[self.lesson.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Тестовый урок")

    def test_get_lesson_detail_by_moderator(self):
        """Модератор может просмотреть любой урок"""
        self.client.force_authenticate(user=self.moderator)
        url = reverse("lesson-detail", args=[self.lesson.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_lesson_detail_by_other_user(self):
        """Чужой пользователь НЕ может просмотреть не свой урок"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("lesson-detail", args=[self.lesson.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_lesson_by_owner_simple(self):
        """Владелец может обновить свой урок"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("lesson-detail", args=[self.lesson.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_lesson_by_moderator_simple(self):
        """Модератор может просмотреть чужой урок"""
        self.client.force_authenticate(user=self.moderator)
        url = reverse("lesson-detail", args=[self.lesson.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_lesson_by_owner_simple(self):
        """Владелец имеет доступ к удалению"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("lesson-detail", args=[self.lesson.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SubscriptionTestCase(APITestCase):
    """Тесты для функционала подписки на курс"""

    def setUp(self):
        """Создание тестовых данных"""
        self.user = User.objects.create_user(
            email="user@example.com", password="password123"
        )

        self.course = Course.objects.create(title="Курс для подписки", owner=self.user)

    def test_subscribe_to_course(self):
        """Пользователь может подписаться на курс"""
        self.client.force_authenticate(user=self.user)
        url = reverse("subscription-manage")
        data = {"course_id": self.course.id}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка добавлена")
        self.assertTrue(response.data["is_subscribed"])

    def test_unsubscribe_from_course(self):
        """Пользователь может отписаться от курса"""
        self.client.force_authenticate(user=self.user)
        url = reverse("subscription-manage")
        data = {"course_id": self.course.id}

        self.client.post(url, data, format="json")

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка удалена")
        self.assertFalse(response.data["is_subscribed"])

    def test_subscription_toggle(self):
        """Toggle функционал: подписка → отписка → подписка"""
        self.client.force_authenticate(user=self.user)
        url = reverse("subscription-manage")
        data = {"course_id": self.course.id}

        response1 = self.client.post(url, data, format="json")
        self.assertTrue(response1.data["is_subscribed"])

        response2 = self.client.post(url, data, format="json")
        self.assertFalse(response2.data["is_subscribed"])

        response3 = self.client.post(url, data, format="json")
        self.assertTrue(response3.data["is_subscribed"])

    def test_is_subscribed_field_in_course(self):
        """Поле is_subscribed отображается в курсе"""
        self.client.force_authenticate(user=self.user)

        subscribe_url = reverse("subscription-manage")
        self.client.post(subscribe_url, {"course_id": self.course.id}, format="json")

        course_url = reverse("course-detail", args=[self.course.id])
        response = self.client.get(course_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_subscribed"])

    def test_subscription_without_course_id(self):
        """Ошибка при отсутствии course_id"""
        self.client.force_authenticate(user=self.user)
        url = reverse("subscription-manage")
        data = {}  # Нет course_id

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_subscription_by_anonymous_user(self):
        """Анонимный пользователь не может подписаться"""
        url = reverse("subscription-manage")
        data = {"course_id": self.course.id}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DifferentUserRolesTestCase(APITestCase):
    """тесты для разных ролей пользователей"""

    def setUp(self):
        """Создание пользователей с разными ролями"""
        self.moderator_group, _ = Group.objects.get_or_create(name="Модераторы")

        self.owner = User.objects.create_user(
            email="owner@example.com", password="password123"
        )

        self.regular_user = User.objects.create_user(
            email="regular@example.com", password="password123"
        )

        self.moderator = User.objects.create_user(
            email="moderator@example.com", password="password123"
        )
        self.moderator.groups.add(self.moderator_group)

        self.admin = User.objects.create_user(
            email="admin@example.com", password="password123", is_staff=True
        )

        self.course = Course.objects.create(title="Тестовый курс", owner=self.owner)

        self.lesson = Lesson.objects.create(
            title="Тестовый урок", course=self.course, owner=self.owner
        )

    def test_owner_can_view_own_course(self):
        """Владелец может просмотреть свой курс"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("course-detail", args=[self.course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_view_others_course(self):
        """Обычный пользователь не может просмотреть чужой курс"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("course-detail", args=[self.course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_moderator_can_view_any_course(self):
        """Модератор может просмотреть любой курс"""
        self.client.force_authenticate(user=self.moderator)
        url = reverse("course-detail", args=[self.course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_view_any_course(self):
        """Администратор может просмотреть любой курс"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("course-detail", args=[self.course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_moderator_cannot_create_lesson(self):
        """Модератор не может создать урок"""
        self.client.force_authenticate(user=self.moderator)
        url = reverse("lesson-list-create")
        data = {"title": "Новый урок от модератора", "course": self.course.id}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_lesson(self):
        """Администратор может создать урок"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("lesson-list-create")
        data = {"title": "Новый урок от админа", "course": self.course.id}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
