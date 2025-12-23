import stripe
from django.conf import settings
from django.core.exceptions import ValidationError

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(name, description=None):
    """Создает продукт в Stripe."""
    try:
        product = stripe.Product.create(name=name, description=description, active=True)
        return product.id
    except stripe.error.StripeError as e:
        raise ValidationError(f"Ошибка создания продукта в Stripe: {e.user_message}")


def create_stripe_price(product_id, amount, currency="rub"):
    """Создает цену для продукта в Stripe."""
    try:
        unit_amount = int(amount * 100)

        price = stripe.Price.create(
            product=product_id,
            unit_amount=unit_amount,
            currency=currency,
            recurring=None,
            tax_behavior="unspecified",
        )
        return price.id
    except stripe.error.StripeError as e:
        raise ValidationError(f"Ошибка создания цены в Stripe: {e.user_message}")


def create_stripe_checkout_session(price_id, success_url, cancel_url, metadata=None):
    """Создает сессию Checkout в Stripe и возвращает ссылку на оплату."""
    try:
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata or {},
            payment_method_types=["card"],
        )
        return {
            "session_id": session.id,
            "payment_link": session.url,
            "payment_status": session.payment_status,
        }
    except stripe.error.StripeError as e:
        raise ValidationError(
            f"Ошибка создания сессии оплаты в Stripe: {e.user_message}"
        )


def retrieve_stripe_session(session_id):
    """Получает информацию о сессии оплаты в Stripe."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "id": session.id,
            "payment_status": session.payment_status,
            "amount_total": session.amount_total,
            "currency": session.currency,
            "customer_details": session.customer_details,
        }
    except stripe.error.StripeError as e:
        raise ValidationError(f"Ошибка получения информации о сессии: {e.user_message}")
