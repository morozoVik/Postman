import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

from .models import Course, Lesson, Subscription

logger = logging.getLogger(__name__)


@shared_task
def send_new_lesson_notifications():
    """Отправляет уведомления о новых уроках за последние 24 часа"""
    try:
        yesterday = timezone.now() - timedelta(days=1)

        new_lessons = Lesson.objects.filter(date_created__gte=yesterday).select_related(
            "course"
        )

        if not new_lessons.exists():
            logger.info("Нет новых уроков за последние 24 часа")
            return "Нет новых уроков за последние 24 часа"

        for lesson in new_lessons:
            subscriptions = Subscription.objects.filter(
                course=lesson.course, is_active=True
            ).select_related("user")

            for subscription in subscriptions:
                try:
                    user = subscription.user

                    subject = f'Новый урок в курсе "{lesson.course.title}"'
                    message = f"""
                    Уважаемый(ая) {user.email},

                    В курсе "{lesson.course.title}" добавлен новый урок:

                    "{lesson.title}"

                    Описание: {lesson.description[:100]}...

                    Перейдите в личный кабинет, чтобы просмотреть новый урок:
                    http://localhost:8000/courses/{lesson.course.id}/lessons/{lesson.id}/

                    С уважением,
                    Команда Postman
                    """

                    send_mail(
                        subject=subject,
                        message=message.strip(),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )

                    logger.info(
                        f"Уведомление отправлено пользователю {user.email} о новом уроке {lesson.id}"
                    )

                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке уведомления пользователю {user.email}: {str(e)}"
                    )
                    continue

        return f"Отправлено уведомлений о {new_lessons.count()} новых уроках"

    except Exception as e:
        logger.error(f"Ошибка в задаче send_new_lesson_notifications: {str(e)}")
        raise


@shared_task
def check_expiring_subscriptions():
    """Проверяет подписки, которые скоро истекают"""
    try:
        three_days_from_now = timezone.now() + timedelta(days=3)
        expiring_subscriptions = Subscription.objects.filter(
            is_active=True,
            date_end__lte=three_days_from_now,
            date_end__gt=timezone.now(),
        ).select_related("user", "course")

        for subscription in expiring_subscriptions:
            try:
                user = subscription.user
                days_left = (subscription.date_end - timezone.now()).days

                subject = f"Ваша подписка скоро истекает!"
                message = f"""
                Уважаемый(ая) {user.email},

                Ваша подписка на курс "{subscription.course.title}" истекает через {days_left} дней.
                Дата окончания: {subscription.date_end.strftime('%d.%m.%Y')}

                Чтобы продолжить обучение, продлите подписку в личном кабинете.

                С уважением,
                Команда Postman
                """

                send_mail(
                    subject=subject,
                    message=message.strip(),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                logger.info(
                    f"Уведомление об истечении подписки отправлено пользователю {user.email}"
                )

            except Exception as e:
                logger.error(
                    f"Ошибка при отправке уведомления об истечении подписки: {str(e)}"
                )
                continue

        return f"Проверено {expiring_subscriptions.count()} истекающих подписок"

    except Exception as e:
        logger.error(f"Ошибка в задаче check_expiring_subscriptions: {str(e)}")
        raise


@shared_task
def update_course_statistics():
    """Обновляет статистику курсов (количество уроков, подписчиков и т.д.)"""
    try:
        courses = Course.objects.all()
        updated_count = 0

        for course in courses:
            try:
                lesson_count = Lesson.objects.filter(course=course).count()

                subscriber_count = Subscription.objects.filter(
                    course=course, is_active=True
                ).count()

                if (
                    hasattr(course, "lesson_count")
                    and course.lesson_count != lesson_count
                ):
                    course.lesson_count = lesson_count
                    course.save(update_fields=["lesson_count"])
                    updated_count += 1

                if (
                    hasattr(course, "subscriber_count")
                    and course.subscriber_count != subscriber_count
                ):
                    course.subscriber_count = subscriber_count
                    course.save(update_fields=["subscriber_count"])
                    updated_count += 1

            except Exception as e:
                logger.error(
                    f"Ошибка при обновлении статистики курса {course.id}: {str(e)}"
                )
                continue

        logger.info(f"Обновлена статистика для {updated_count} курсов")
        return f"Обновлена статистика для {updated_count} курсов"

    except Exception as e:
        logger.error(f"Ошибка в задаче update_course_statistics: {str(e)}")
        raise
