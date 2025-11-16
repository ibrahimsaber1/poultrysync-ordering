from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Product
from .serializers import ProductSerializer


def index_view(request):
    """
    Index page showing product creation form and products table.
    As per requirements: "Simple HTML Interface (index page): 
    Product creation form + table listing added products"
    """
    if request.user.is_authenticated:
        products = Product.objects.filter(
            company=request.user.company
        ).select_related('company', 'created_by').order_by('-created_at')
    else:
        products = []
    
    context = {
        'products': products,
        'now': timezone.now()
    }
    
    return render(request, 'index.html', context)


@login_required
def create_product(request):
    """Handle product creation from form"""
    if request.method == 'POST':
        if request.user.role == 'viewer':
            messages.error(request, 'Viewers cannot add products.')
            return redirect('index')
        try:
            name = request.POST.get('name')
            price = request.POST.get('price')
            stock = request.POST.get('stock')
            
            if not all([name, price, stock]):
                messages.error(request, 'All fields are required.')
                return redirect('index')
            
            if Product.objects.filter(company=request.user.company, name=name).exists():
                messages.error(request, f'Product "{name}" already exists.')
                return redirect('index')
            
            product = Product.objects.create(
                company=request.user.company,
                name=name,
                price=float(price),
                stock=int(stock),
                created_by=request.user,
            )
            
            messages.success(request, f'Product "{product.name}" created successfully!')
            
        except ValueError:
            messages.error(request, 'Invalid price or stock value.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('index')


# API Views (keep these for API access)
class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).select_related('company', 'created_by').order_by('-created_at')


class ProductBulkDeleteAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        product_ids = request.data.get('product_ids', [])

        if not product_ids:
            return Response(
                {'error': 'No product IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        products = Product.objects.filter(
            id__in=product_ids,
            company=request.user.company,
            is_active=True
        )

        if not products.exists():
            return Response(
                {'error': 'No valid products found'},
                status=status.HTTP_404_NOT_FOUND
            )

        count = products.update(is_active=False)

        return Response({
            'success': True,
            'message': f'{count} product(s) marked as inactive',
            'count': count
        }, status=status.HTTP_200_OK)
