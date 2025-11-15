from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create_page, name='create'),
    
    path('api/create/', views.OrderCreateAPIView.as_view(), name='api-create'),
    path('api/export/', views.OrderExportAPIView.as_view(), name='export'),
]
