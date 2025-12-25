import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import Payment
from .services import retrieve_stripe_session

logger = logging.getLogger(__name__)


@shared_task
def check_payment_status():
    """Проверяет статусы незавершенных платежей в Stripe"""
    try:
        one_hour_ago = timezone.now() - timedelta(hours=1)
        pending_payments = Payment.objects.filter(
            stripe_payment_status__in=[
                "pending",
                "requires_payment_method",
                "requires_action",
            ],
            payment_date__gte=one_hour_ago,
        )

        updated_count = 0
        for payment in pending_payments:
            try:
                session = retrieve_stripe_session(payment.stripe_session_id)
                if (
                    session
                    and session.get("payment_status") != payment.stripe_payment_status
                ):
                    payment.stripe_payment_status = session.get("payment_status")
                    payment.save(update_fields=["stripe_payment_status"])
                    updated_count += 1

                    if session.get("payment_status") == "paid":
                        send_payment_success_email.delay(payment.id)

            except Exception as e:
                logger.error(f"Ошибка при проверке платежа {payment.id}: {str(e)}")
                continue

        logger.info(
            f"Проверено {pending_payments.count()} платежей, обновлено {updated_count}"
        )
        return (
            f"Проверено {pending_payments.count()} платежей, обновлено {updated_count}"
        )

    except Exception as e:
        logger.error(f"Ошибка в задаче check_payment_status: {str(e)}")
        raise


@shared_task
def send_payment_success_email(payment_id):
    """Отправляет email об успешной оплате"""
    try:
        payment = Payment.objects.get(id=payment_id)
        user = payment.user

        subject = "Оплата успешно завершена!"
        message = f"""
        Уважаемый(ая) {user.email},

        Ваш платеж на сумму {payment.amount} руб. успешно обработан.

        Детали платежа:
        - Номер платежа: {payment.id}
        - Дата: {payment.date_created.strftime('%d.%m.%Y %H:%M')}
        - Статус: Успешно

        Спасибо за использование нашей платформы!

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

        logger.info(f"Email отправлен пользователю {user.email} о платеже {payment_id}")
        return True

    except Payment.DoesNotExist:
        logger.error(f"Платеж {payment_id} не найден")
        return False
    except Exception as e:
        logger.error(f"Ошибка при отправке email: {str(e)}")
        raise


@shared_task
def cleanup_old_payments():
    """Очищает старые неудачные платежи (старше 30 дней)"""
    try:
        thirty_days_ago = timezone.now() - timedelta(days=30)
        old_failed_payments = Payment.objects.filter(
            stripe_payment_status__in=["canceled", "failed", "expired"],
            date_created__lt=thirty_days_ago,
        )

        count = old_failed_payments.count()
        old_failed_payments.delete()

        logger.info(f"Удалено {count} старых неудачных платежей")
        return f"Удалено {count} старых неудачных платежей"

    except Exception as e:
        logger.error(f"Ошибка при очистке старых платежей: {str(e)}")
        raise


@shared_task
def test_task(message="Тестовая задача выполнена!"):
    """
    Простая тестовая задача для проверки работы Celery
    """
    from django.utils import timezone

    print(f"[{timezone.now()}] Test task executed: {message}")
    logger.info(f"Test task executed: {message}")
    return f"Тестовая задача выполнена: {message}"
