from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create_page, name='create-page'),
    path('api/', views.OrderCreateView.as_view(), name='api-create'),
    path('api/export/', views.OrderExportView.as_view(), name='api-export'),
]
