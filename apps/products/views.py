"""
Views for products app.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import BusinessScopedMixin
from apps.common.permissions import IsBusinessAdminOrReadOnly
from apps.common.permissions import IsBusinessMember
from apps.products.models import Package
from apps.products.models import Product
from apps.products.serializers import PackageCreateSerializer
from apps.products.serializers import PackageListSerializer
from apps.products.serializers import PackagePriceCalculatorSerializer
from apps.products.serializers import PackagePriceResponseSerializer
from apps.products.serializers import PackageSerializer
from apps.products.serializers import ProductCreateSerializer
from apps.products.serializers import ProductSerializer


class ProductListCreateView(BusinessScopedMixin, generics.ListCreateAPIView):
    """
    API endpoint to list and create products.
    """

    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'base_price', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method == 'POST':
            return ProductCreateSerializer
        return ProductSerializer


class ProductDetailView(BusinessScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for product detail operations.
    """

    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateSerializer
        return ProductSerializer


class PackageListCreateView(BusinessScopedMixin, generics.ListCreateAPIView):
    """
    API endpoint to list and create packages.
    """

    queryset = Package.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'base_price', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method == 'POST':
            return PackageCreateSerializer
        if self.request.query_params.get('list', '').lower() == 'true':
            return PackageListSerializer
        return PackageSerializer


class PackageDetailView(BusinessScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for package detail operations.
    """

    queryset = Package.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return PackageCreateSerializer
        return PackageSerializer


class PackagePriceCalculatorView(APIView):
    """
    API endpoint to calculate package price for given pax.
    """

    permission_classes = [IsAuthenticated, IsBusinessMember]

    def post(self, request, pk):
        """
        Calculate package price based on pax count.
        """
        try:
            package = Package.objects.get(
                pk=pk,
                business=request.user.current_business
            )
        except Package.DoesNotExist:
            return Response(
                {'error': 'Package not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PackagePriceCalculatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pax_count = serializer.validated_data['pax_count']

        if package.max_pax and pax_count > package.max_pax:
            return Response(
                {'error': f'Maximum pax for this package is {package.max_pax}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_price = package.calculate_price(pax_count)

        response_data = {
            'package_id': package.id,
            'package_name': package.name,
            'pax_count': pax_count,
            'base_price': package.base_price,
            'total_price': total_price
        }

        response_serializer = PackagePriceResponseSerializer(response_data)
        return Response(response_serializer.data)
