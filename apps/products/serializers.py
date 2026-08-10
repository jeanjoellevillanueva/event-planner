"""
Serializers for products app.
"""

from rest_framework import serializers

from apps.common.mixins import TimezoneAwareMixin
from apps.products.models import Package
from apps.products.models import PackageItem
from apps.products.models import Product


class ProductSerializer(TimezoneAwareMixin, serializers.ModelSerializer):
    """
    Serializer for Product model.
    """

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'base_price',
            'unit', 'image', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating products.
    """

    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'base_price', 'unit', 'image']


class PackageItemSerializer(serializers.ModelSerializer):
    """
    Serializer for PackageItem model.
    """

    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.base_price',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = PackageItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'notes']


class PackageSerializer(TimezoneAwareMixin, serializers.ModelSerializer):
    """
    Serializer for Package model.
    """

    items = PackageItemSerializer(source='packageitem_set', many=True, read_only=True)

    class Meta:
        model = Package
        fields = [
            'id', 'name', 'description', 'base_price', 'min_pax', 'max_pax',
            'price_per_additional_pax', 'inclusions', 'image', 'is_active',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PackageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating packages.
    """

    items = PackageItemSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Package
        fields = [
            'name', 'description', 'base_price', 'min_pax', 'max_pax',
            'price_per_additional_pax', 'inclusions', 'image', 'items'
        ]

    def validate(self, attrs):
        """
        Validate min_pax and max_pax relationship.
        """
        min_pax = attrs.get('min_pax', 1)
        max_pax = attrs.get('max_pax')

        if max_pax and max_pax < min_pax:
            raise serializers.ValidationError({
                'max_pax': 'max_pax must be greater than or equal to min_pax'
            })

        return attrs

    def create(self, validated_data):
        """
        Create package with items.
        """
        items_data = validated_data.pop('items', [])
        package = super().create(validated_data)

        for item_data in items_data:
            PackageItem.objects.create(package=package, **item_data)

        return package

    def update(self, instance, validated_data):
        """
        Update package with items.
        """
        items_data = validated_data.pop('items', None)
        package = super().update(instance, validated_data)

        if items_data is not None:
            instance.packageitem_set.all().delete()
            for item_data in items_data:
                PackageItem.objects.create(package=package, **item_data)

        return package


class PackageListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for package lists.
    """

    class Meta:
        model = Package
        fields = ['id', 'name', 'base_price', 'min_pax', 'max_pax', 'is_active']


class PackagePriceCalculatorSerializer(serializers.Serializer):
    """
    Serializer for calculating package price.
    """

    pax_count = serializers.IntegerField(min_value=1)


class PackagePriceResponseSerializer(serializers.Serializer):
    """
    Serializer for package price response.
    """

    package_id = serializers.IntegerField()
    package_name = serializers.CharField()
    pax_count = serializers.IntegerField()
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)
