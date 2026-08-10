"""
Tests for products models.
"""

import pytest
from decimal import Decimal

from apps.products.models import Package
from apps.products.models import Product


@pytest.mark.django_db
class TestProductModel:
    """
    Tests for Product model.
    """

    def test_create_product(self, business_factory):
        """
        Should create product with correct fields.
        """
        business = business_factory()
        product = Product.objects.create(
            business=business,
            name='Photography',
            category='service',
            base_price=5000.00
        )

        assert product.name == 'Photography'
        assert product.base_price == Decimal('5000.00')
        assert str(product) == f'Photography ({business.name})'


@pytest.mark.django_db
class TestPackageModel:
    """
    Tests for Package model.
    """

    def test_create_package(self, business_factory):
        """
        Should create package with correct fields.
        """
        business = business_factory()
        package = Package.objects.create(
            business=business,
            name='Premium Package',
            base_price=50000.00,
            min_pax=50,
            max_pax=100
        )

        assert package.name == 'Premium Package'
        assert package.min_pax == 50
        assert package.max_pax == 100

    def test_calculate_price_at_min_pax(self, package_factory):
        """
        Should return base price at min pax.
        """
        package = package_factory(
            base_price=10000,
            min_pax=50,
            price_per_additional_pax=100
        )

        assert package.calculate_price(50) == Decimal('10000')

    def test_calculate_price_below_min_pax(self, package_factory):
        """
        Should return base price below min pax.
        """
        package = package_factory(
            base_price=10000,
            min_pax=50,
            price_per_additional_pax=100
        )

        assert package.calculate_price(30) == Decimal('10000')

    def test_calculate_price_above_min_pax(self, package_factory):
        """
        Should add per-pax cost above min.
        """
        package = package_factory(
            base_price=10000,
            min_pax=50,
            price_per_additional_pax=100
        )

        assert package.calculate_price(75) == Decimal('12500')

    def test_calculate_price_at_max_pax(self, package_factory):
        """
        Should calculate correctly at max pax.
        """
        package = package_factory(
            base_price=10000,
            min_pax=50,
            max_pax=100,
            price_per_additional_pax=100
        )

        assert package.calculate_price(100) == Decimal('15000')
