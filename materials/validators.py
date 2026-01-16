from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_youtube_url(value):
    """
    Валидатор для проверки, что ссылка ведет только на youtube.com или youtu.be
    """
    if not value:
        return

    if not value.startswith(("http://", "https://")):
        raise ValidationError(_("URL должен начинаться с http:// или https://"))

    try:
        parsed_url = urlparse(value)

        if not parsed_url.netloc:
            raise ValidationError(_("Некорректный URL адрес"))

        domain = parsed_url.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        allowed_domains = ["youtube.com", "youtu.be"]

        if domain not in allowed_domains:
            if not (domain.endswith(".youtube.com") and domain.count(".") == 2):
                raise ValidationError(
                    _("Разрешены только ссылки на YouTube (youtube.com или youtu.be)")
                )

    except ValidationError:
        raise
    except Exception:
        raise ValidationError(_("Некорректный URL адрес"))
