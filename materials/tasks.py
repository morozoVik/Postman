import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

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
                course=lesson.course
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

                subscriber_count = Subscription.objects.filter(course=course).count()

                logger.info(
                    f"Курс '{course.title}': {lesson_count} уроков, {subscriber_count} подписчиков"
                )

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


@shared_task
def send_course_update_notifications(course_id, update_type="обновлен"):
    """Отправляет уведомления об обновлении курса всем подписчикам"""
    try:
        course = Course.objects.get(id=course_id)

        logger.info(f"Начинаем отправку уведомлений для курса: {course.title}")

        subscriptions = Subscription.objects.filter(course=course)

        logger.info(f"Найдено подписок: {subscriptions.count()}")

        if not subscriptions.exists():
            logger.info(f"Нет подписчиков для курса {course.title}")
            return f"Нет подписчиков для курса {course.title}"

        email_count = 0
        errors_count = 0

        for subscription in subscriptions:
            try:
                user = subscription.user

                logger.info(f"Обработка пользователя: {user.email}")

                subject = f'Курс "{course.title}" {update_type}'

                last_updated_str = (
                    course.last_updated.strftime("%d.%m.%Y %H:%M")
                    if course.last_updated
                    else "недавно"
                )

                message = f"""
                Уважаемый(ая) {user.email},

                Курс "{course.title}" был {update_type}.

                Последнее обновление: {last_updated_str}

                Перейдите в личный кабинет, чтобы посмотреть изменения:
                http://localhost:8000/api/courses/{course.id}/

                Если вы не хотите получать уведомления об обновлениях этого курса,
                отпишитесь от него в личном кабинете.

                С уважением,
                Команда Postman
                """

                logger.info(f"Отправка email пользователю {user.email}...")

                send_mail(
                    subject=subject,
                    message=message.strip(),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                email_count += 1
                logger.info(f"Уведомление отправлено пользователю {user.email}")

            except Exception as e:
                errors_count += 1
                logger.error(
                    f"Ошибка при отправке уведомления пользователю {user.email}: {str(e)}"
                )
                continue

        course.last_notification_sent = timezone.now()
        course.save(update_fields=["last_notification_sent"])

        logger.info(
            f"Итого: отправлено {email_count} уведомлений, ошибок: {errors_count}"
        )
        return (
            f"Отправлено {email_count} уведомлений об обновлении курса {course.title}"
        )

    except Course.DoesNotExist:
        logger.error(f"Курс с ID {course_id} не найден")
        return f"Курс с ID {course_id} не найден"
    except Exception as e:
        logger.error(f"Ошибка в задаче send_course_update_notifications: {str(e)}")
        raise


@shared_task
def check_and_send_course_updates(course_id, force_send=False):
    """Проверяет, нужно ли отправлять уведомление об обновлении курса(проверка 4-х часового интервала)"""
    try:
        course = Course.objects.get(id=course_id)

        if (
            force_send
            or not course.last_notification_sent
            or (timezone.now() - course.last_notification_sent) > timedelta(hours=4)
        ):

            return send_course_update_notifications.delay(course_id, "обновлен")
        else:
            hours_since_last_notification = (
                timezone.now() - course.last_notification_sent
            ).seconds / 3600
            logger.info(
                f"Уведомление для курса {course.title} не отправлено. "
                f"Прошло только {hours_since_last_notification:.1f} часов с последней отправки"
            )
            return f"Уведомление не отправлено (прошло {hours_since_last_notification:.1f} часов)"

    except Course.DoesNotExist:
        logger.error(f"Курс с ID {course_id} не найден")
        return f"Курс с ID {course_id} не найден"
    except Exception as e:
        logger.error(f"Ошибка в задаче check_and_send_course_updates: {str(e)}")
        raise


@shared_task
def send_lesson_update_notifications(lesson_id, update_type="обновлен"):
    """Отправляет уведомления об обновлении урока всем подписчикам курса"""
    try:
        lesson = Lesson.objects.select_related("course").get(id=lesson_id)
        course = lesson.course

        return send_course_update_notifications.delay(
            course.id, f"обновлен (изменен урок: {lesson.title})"
        )

    except Lesson.DoesNotExist:
        logger.error(f"Урок с ID {lesson_id} не найден")
        return f"Урок с ID {lesson_id} не найден"
    except Exception as e:
        logger.error(f"Ошибка в задаче send_lesson_update_notifications: {str(e)}")
        raise


@shared_task
def test_email_notification():
    """Тестовая задача для проверки отправки email"""
    try:
        subject = "Тестовое уведомление от Postman"
        message = "Это тестовое уведомление об обновлении курса."

        test_email = "Morozof30@yandex.ru"

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )

        return f"Тестовое письмо отправлено на {test_email}"

    except Exception as e:
        logger.error(f"Ошибка в тестовой задаче: {str(e)}")
        raise
