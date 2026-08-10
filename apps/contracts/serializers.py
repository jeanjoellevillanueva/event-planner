"""
Serializers for contracts app.
"""

from rest_framework import serializers

from apps.common.mixins import TimezoneAwareMixin
from apps.contracts.models import Contract
from apps.contracts.models import ContractTemplate


class ContractTemplateSerializer(TimezoneAwareMixin, serializers.ModelSerializer):
    """
    Serializer for ContractTemplate model.
    """

    class Meta:
        model = ContractTemplate
        fields = [
            'id', 'name', 'description', 'content',
            'is_default', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContractTemplateCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating contract templates.
    """

    class Meta:
        model = ContractTemplate
        fields = ['name', 'description', 'content', 'is_default']


class ContractTemplateListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for template lists.
    """

    class Meta:
        model = ContractTemplate
        fields = ['id', 'name', 'is_default', 'is_active']


class ContractSerializer(TimezoneAwareMixin, serializers.ModelSerializer):
    """
    Serializer for Contract model.
    """

    template_name = serializers.CharField(source='template.name', read_only=True)
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)
    client_name = serializers.CharField(source='booking.client.name', read_only=True)
    event_date = serializers.DateField(source='booking.event_date', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)

    class Meta:
        model = Contract
        fields = [
            'id', 'booking_id', 'client_name', 'event_date',
            'template', 'template_name', 'rendered_content',
            'generated_file', 'signed_file', 'status',
            'signed_at', 'signed_by', 'notes',
            'generated_by', 'generated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'rendered_content', 'generated_file', 'signed_file',
            'signed_at', 'generated_by', 'created_at', 'updated_at'
        ]


class ContractGenerateSerializer(serializers.Serializer):
    """
    Serializer for generating contract.
    """

    template_id = serializers.IntegerField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class ContractSignSerializer(serializers.Serializer):
    """
    Serializer for marking contract as signed.
    """

    signed_by = serializers.CharField(max_length=200)
    signed_file = serializers.FileField(required=False)
