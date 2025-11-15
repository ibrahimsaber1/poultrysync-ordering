from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from .models import Product
from .serializers import ProductSerializer

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(
            company=self.request.user.company,
            is_active=True
        )

class ProductDeleteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        product_ids = request.data.get('product_ids', [])
        
        if not product_ids:
            return Response(
                {'error': 'No product IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        products = Product.objects.filter(
            id__in=product_ids,
            company=request.user.company
        )
        
        count = products.update(is_active=False)
        
        return Response({
            'message': f'{count} products marked as inactive',
            'count': count
        })

def index_view(request):
    if request.user.is_authenticated:
        products = Product.objects.filter(
            company=request.user.company
        ).order_by('-created_at')
    else:
        products = []
    
    return render(request, 'index.html', {'products': products})
