from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from materials.models import Course, Lesson


class Command(BaseCommand):
    help = "Создает группы пользователей и назначает права"

    def handle(self, *args, **options):
        moderator_group, created = Group.objects.get_or_create(name="Модераторы")

        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Модераторы" создана'))
        else:
            self.stdout.write(self.style.WARNING('Группа "Модераторы" уже существует'))

        course_content_type = ContentType.objects.get_for_model(Course)
        lesson_content_type = ContentType.objects.get_for_model(Lesson)

        course_permissions = Permission.objects.filter(
            content_type=course_content_type,
            codename__in=["view_course", "change_course"],
        )

        lesson_permissions = Permission.objects.filter(
            content_type=lesson_content_type,
            codename__in=["view_lesson", "change_lesson"],
        )

        moderator_group.permissions.add(*course_permissions)
        moderator_group.permissions.add(*lesson_permissions)

        self.stdout.write(
            self.style.SUCCESS(
                f"Назначено {course_permissions.count() + lesson_permissions.count()} "
                f'разрешений группе "Модераторы"'
            )
        )

        author_group, created = Group.objects.get_or_create(name="Авторы")

        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Авторы" создана'))

        all_course_permissions = Permission.objects.filter(
            content_type=course_content_type
        )

        all_lesson_permissions = Permission.objects.filter(
            content_type=lesson_content_type
        )

        author_group.permissions.add(*all_course_permissions)
        author_group.permissions.add(*all_lesson_permissions)

        self.stdout.write(
            self.style.SUCCESS(
                f"Назначено {all_course_permissions.count() + all_lesson_permissions.count()} "
                f'разрешений группе "Авторы"'
            )
        )
