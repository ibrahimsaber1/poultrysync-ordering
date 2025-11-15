from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('api/', views.ProductListView.as_view(), name='api-list'),
    path('api/delete/', views.ProductDeleteView.as_view(), name='api-delete'),
]
