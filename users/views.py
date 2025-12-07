from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]

    filterset_fields = ["payment_method", "paid_course", "paid_lesson"]

    ordering_fields = ["payment_date", "amount"]
    ordering = ["-payment_date"]
