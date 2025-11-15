from django.urls import path
from .views import OrderCreateAPIView, OrderExportAPIView

app_name = 'orders'

urlpatterns = [
    path('', OrderCreateAPIView.as_view(), name='api-create'),
    path('export/', OrderExportAPIView.as_view(), name='api-export'),
]
