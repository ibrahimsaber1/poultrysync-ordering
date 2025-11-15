from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListAPIView.as_view(), name='list'),
    path('delete/', views.ProductBulkDeleteAPIView.as_view(), name='bulk-delete'),
]
