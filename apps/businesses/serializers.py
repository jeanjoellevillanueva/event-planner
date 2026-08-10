"""
Serializers for businesses app.
"""

from rest_framework import serializers

from apps.businesses.models import Business


class BusinessSerializer(serializers.ModelSerializer):
    """
    Serializer for Business model.
    """

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'slug', 'business_type', 'logo', 'description',
            'email', 'phone', 'address', 'website', 'settings', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class BusinessCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a business.
    """

    class Meta:
        model = Business
        fields = [
            'name', 'business_type', 'logo', 'description',
            'email', 'phone', 'address', 'website'
        ]


class BusinessDashboardSerializer(serializers.Serializer):
    """
    Serializer for business dashboard stats.
    """

    total_clients = serializers.IntegerField()
    total_bookings = serializers.IntegerField()
    pending_bookings = serializers.IntegerField()
    confirmed_bookings = serializers.IntegerField()
    upcoming_events = serializers.IntegerField()
    monthly_bookings = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_packages = serializers.IntegerField()
    team_members = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
