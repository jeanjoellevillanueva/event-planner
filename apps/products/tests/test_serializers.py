"""
Tests for products serializers.
"""

import pytest
from rest_framework.test import APIRequestFactory

from apps.products.models import Package
from apps.products.models import PackageItem
from apps.products.models import Product
from apps.products.serializers import PackageCreateSerializer
from apps.products.serializers import PackageListSerializer
from apps.products.serializers import PackagePriceCalculatorSerializer
from apps.products.serializers import PackageSerializer
from apps.products.serializers import ProductCreateSerializer
from apps.products.serializers import ProductSerializer


@pytest.mark.django_db
class TestProductSerializer:
    """
    Tests for ProductSerializer.
    """

    def test_serialize_product(self, business_factory):
        """
        Should serialize product with all fields.
        """
        business = business_factory()
        product = Product.objects.create(
            business=business,
            name='Test Product',
            category='service',
            base_price=1000.00,
            unit='per hour'
        )

        serializer = ProductSerializer(product)
        data = serializer.data

        assert data['name'] == 'Test Product'
        assert data['category'] == 'service'
        assert data['base_price'] == '1000.00'
        assert data['unit'] == 'per hour'


@pytest.mark.django_db
class TestProductCreateSerializer:
    """
    Tests for ProductCreateSerializer.
    """

    def test_valid_product_creation(self):
        """
        Should validate correct product data.
        """
        data = {
            'name': 'New Product',
            'category': 'rental',
            'base_price': '500.00',
        }
        serializer = ProductCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_invalid_category(self):
        """
        Should reject invalid category.
        """
        data = {
            'name': 'New Product',
            'category': 'invalid_category',
            'base_price': '500.00',
        }
        serializer = ProductCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'category' in serializer.errors


@pytest.mark.django_db
class TestPackageSerializer:
    """
    Tests for PackageSerializer.
    """

    def test_serialize_package_with_items(self, business_factory):
        """
        Should serialize package with items.
        """
        business = business_factory()
        product = Product.objects.create(
            business=business,
            name='Test Product',
            category='service',
            base_price=1000.00
        )
        package = Package.objects.create(
            business=business,
            name='Test Package',
            base_price=5000.00,
            min_pax=50,
            max_pax=100
        )
        PackageItem.objects.create(package=package, product=product, quantity=2)

        serializer = PackageSerializer(package)
        data = serializer.data

        assert data['name'] == 'Test Package'
        assert data['min_pax'] == 50
        assert data['max_pax'] == 100
        assert len(data['items']) == 1
        assert data['items'][0]['quantity'] == 2


@pytest.mark.django_db
class TestPackageCreateSerializer:
    """
    Tests for PackageCreateSerializer.
    """

    def test_valid_package_creation(self, authenticated_client):
        """
        Should validate correct package data.
        """
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'name': 'New Package',
            'base_price': '10000.00',
            'min_pax': 50,
            'max_pax': 150,
        }
        serializer = PackageCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors

    def test_max_pax_less_than_min_pax_rejected(self, authenticated_client):
        """
        Should reject max_pax < min_pax.
        """
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'name': 'Invalid Package',
            'base_price': '10000.00',
            'min_pax': 100,
            'max_pax': 50,
        }
        serializer = PackageCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'max_pax' in serializer.errors

    def test_create_package_with_items(self, authenticated_client):
        """
        Should create package with product items.
        """
        product = Product.objects.create(
            business=authenticated_client.business,
            name='Test Product',
            category='service',
            base_price=1000.00
        )

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'name': 'Package With Items',
            'base_price': '10000.00',
            'min_pax': 50,
            'items': [{'product': product.id, 'quantity': 3}]
        }
        serializer = PackageCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors

        package = serializer.save(business=authenticated_client.business)
        assert package.packageitem_set.count() == 1
        assert package.packageitem_set.first().quantity == 3

    def test_items_from_other_business_rejected(self, authenticated_client, business_factory):
        """
        Should reject items from different business.
        """
        other_business = business_factory(name='Other Business')
        other_product = Product.objects.create(
            business=other_business,
            name='Other Product',
            category='service',
            base_price=1000.00
        )

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'name': 'Package With Bad Items',
            'base_price': '10000.00',
            'min_pax': 50,
            'items': [{'product': other_product.id, 'quantity': 1}]
        }
        serializer = PackageCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with pytest.raises(Exception):
            serializer.save(business=authenticated_client.business)


class TestPackagePriceCalculatorSerializer:
    """
    Tests for PackagePriceCalculatorSerializer.
    """

    def test_valid_pax_count(self):
        """
        Should validate positive pax count.
        """
        serializer = PackagePriceCalculatorSerializer(data={'pax_count': 100})
        assert serializer.is_valid()

    def test_zero_pax_rejected(self):
        """
        Should reject zero pax count.
        """
        serializer = PackagePriceCalculatorSerializer(data={'pax_count': 0})
        assert not serializer.is_valid()

    def test_negative_pax_rejected(self):
        """
        Should reject negative pax count.
        """
        serializer = PackagePriceCalculatorSerializer(data={'pax_count': -5})
        assert not serializer.is_valid()
