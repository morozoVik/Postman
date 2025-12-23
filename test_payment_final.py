import os
import django
import requests

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from materials.models import Course

BASE_URL = "http://127.0.0.1:8000"


def main():
    print("=" * 70)
    print("ТЕСТ STRIPE ПОСЛЕ ИСПРАВЛЕНИЯ СЕРИАЛИЗАТОРА")
    print("=" * 70)

    # 1. Выбор курса
    course = Course.objects.first()
    print(f"📚 Курс: {course.title} (ID: {course.id})")

    # 2. Создание нового пользователя (чтобы точно знать пароль)
    from users.models import User
    import random

    test_email = f"test_user_{random.randint(1000, 9999)}@example.com"
    test_password = "TestStripe123"

    try:
        # Удаляем если существует
        User.objects.filter(email=test_email).delete()

        # Создаем нового
        user = User.objects.create_user(
            email=test_email,
            password=test_password,
            first_name="Test",
            last_name="User",
        )
        print(f"👤 Создан пользователь: {user.email}")

    except Exception as e:
        print(f"❌ Ошибка создания пользователя: {e}")
        return

    # 3. Получение JWT токена
    print("\n🔑 Получение JWT токена...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/token/",
            json={"email": test_email, "password": test_password},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code != 200:
            print(f"❌ Ошибка получения токена: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return

        access_token = response.json()["access"]
        print("✅ Токен получен")
        print(f"   Токен (первые 50 символов): {access_token[:50]}...")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return

    # 4. Создание платежа через Stripe
    print("\n💳 Создание платежа через Stripe...")

    # Вариант 1: Без поля user (если исправили сериализатор)
    payment_data = {
        "paid_course": course.id,
        "amount": 1500.00,
        "payment_method": "transfer",
        # Поле user НЕ включаем - оно должно быть read_only
    }

    print(f"   Отправляемые данные: {payment_data}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/payments/", json=payment_data, headers=headers, timeout=15
        )

        print(f"📊 Статус ответа: {response.status_code}")

        if response.status_code == 201:
            result = response.json()

            print("\n" + "=" * 70)
            print("🎉 УСПЕХ! STRIPE ИНТЕГРАЦИЯ РАБОТАЕТ!")
            print("=" * 70)

            print(f"\n📋 Информация о платеже:")
            print(f"   ID: {result.get('id')}")
            print(f"   Пользователь: {result.get('user_email', 'N/A')}")
            print(f"   Сумма: {result.get('amount')} руб.")

            payment_link = result.get("stripe_payment_link")
            if payment_link:
                print(f"\n🔗 Ссылка для оплаты:")
                print(f"   {payment_link}")

                print(f"\n💳 Тестовая карта Stripe:")
                print(f"   Номер: 4242 4242 4242 4242")
                print(f"   Срок: 12/34")
                print(f"   CVC: 567")
                print(f"   Почта: test@example.com")

                print(f"\n📊 Данные Stripe:")
                print(f"   Product ID: {result.get('stripe_product_id')}")
                print(f"   Price ID: {result.get('stripe_price_id')}")
                print(f"   Session ID: {result.get('stripe_session_id')}")
                print(f"   Статус: {result.get('stripe_payment_status')}")

                print(f"\n✅ ЗАДАНИЕ 2 ВЫПОЛНЕНО!")
                print("   Stripe интеграция успешно настроена и работает.")

                # Проверим сохранение в БД
                from users.models import Payment

                payment_in_db = Payment.objects.get(id=result["id"])
                print(f"\n📁 Проверка сохранения в БД:")
                print(f"   Запись создана: ДА")
                print(
                    f"   Stripe ссылка сохранена: {'ДА' if payment_in_db.stripe_payment_link else 'НЕТ'}"
                )
                print(
                    f"   Session ID сохранен: {'ДА' if payment_in_db.stripe_session_id else 'НЕТ'}"
                )

            else:
                print(f"❌ Ссылка на оплату не сгенерирована")

        elif response.status_code == 400:
            error_data = response.json()
            print(f"\n❌ Ошибка 400:")
            print(f"   {error_data}")

            # Если все еще проблема с user
            if "user" in str(error_data):
                print(f"\n🔧 Решение: Нужно исправить PaymentSerializer")
                print(f"   1. Откройте users/serializers.py")
                print(f"   2. Добавьте 'user' в read_only_fields")
                print(f"   3. Или уберите 'user' из fields, если не нужен в ответе")

        else:
            print(f"❌ Ошибка {response.status_code}:")
            print(f"   {response.text[:200]}...")

    except Exception as e:
        print(f"❌ Ошибка при запросе: {e}")

    print("\n" + "=" * 70)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 70)


if __name__ == "__main__":
    main()
