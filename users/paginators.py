from rest_framework.pagination import PageNumberPagination


class PaymentPagination(PageNumberPagination):
    """Пагинация для списка платежей"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserPagination(PageNumberPagination):
    """Пагинация для списка пользователей (опционально)"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

