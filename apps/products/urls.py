"""
URLs for products app.
"""

from django.urls import path

from apps.products.views import PackageDetailView
from apps.products.views import PackageListCreateView
from apps.products.views import PackagePriceCalculatorView
from apps.products.views import ProductDetailView
from apps.products.views import ProductListCreateView

urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product_list_create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('packages/', PackageListCreateView.as_view(), name='package_list_create'),
    path('packages/<int:pk>/', PackageDetailView.as_view(), name='package_detail'),
    path('packages/<int:pk>/calculate-price/', PackagePriceCalculatorView.as_view(), name='package_price'),
]
