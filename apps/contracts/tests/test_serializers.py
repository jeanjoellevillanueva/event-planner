"""
Tests for contracts serializers.
"""

import pytest

from apps.contracts.models import Contract
from apps.contracts.models import ContractTemplate
from apps.contracts.serializers import ContractGenerateSerializer
from apps.contracts.serializers import ContractSerializer
from apps.contracts.serializers import ContractSignSerializer
from apps.contracts.serializers import ContractTemplateCreateSerializer
from apps.contracts.serializers import ContractTemplateSerializer


@pytest.mark.django_db
class TestContractTemplateSerializer:
    """
    Tests for ContractTemplateSerializer.
    """

    def test_serialize_template(self, business_factory):
        """
        Should serialize template with all fields.
        """
        business = business_factory()
        template = ContractTemplate.objects.create(
            business=business,
            name='Standard Contract',
            content='<h1>Contract</h1>',
            is_default=True
        )

        serializer = ContractTemplateSerializer(template)
        data = serializer.data

        assert data['name'] == 'Standard Contract'
        assert data['is_default'] is True
        assert '<h1>Contract</h1>' in data['content']


@pytest.mark.django_db
class TestContractTemplateCreateSerializer:
    """
    Tests for ContractTemplateCreateSerializer.
    """

    def test_valid_template_creation(self):
        """
        Should validate correct template data.
        """
        data = {
            'name': 'New Template',
            'content': '<p>Contract content with {{client_name}}</p>',
            'is_default': False,
        }
        serializer = ContractTemplateCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_content_required(self):
        """
        Should require content field.
        """
        data = {
            'name': 'Empty Template',
            'content': '',
        }
        serializer = ContractTemplateCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'content' in serializer.errors


@pytest.mark.django_db
class TestContractSerializer:
    """
    Tests for ContractSerializer.
    """

    def test_serialize_contract(self, booking_factory, business_factory):
        """
        Should serialize contract with related info.
        """
        business = business_factory()
        booking = booking_factory(business=business)
        template = ContractTemplate.objects.create(
            business=business,
            name='Template',
            content='Content'
        )
        contract = Contract.objects.create(
            booking=booking,
            template=template,
            status='generated'
        )

        serializer = ContractSerializer(contract)
        data = serializer.data

        assert data['booking_id'] == booking.id
        assert data['template_name'] == 'Template'
        assert data['status'] == 'generated'
        assert 'client_name' in data


class TestContractGenerateSerializer:
    """
    Tests for ContractGenerateSerializer.
    """

    def test_valid_generate_request(self):
        """
        Should validate generate request.
        """
        data = {
            'template_id': 1,
            'notes': 'Special instructions',
        }
        serializer = ContractGenerateSerializer(data=data)
        assert serializer.is_valid()

    def test_generate_without_template_id(self):
        """
        Should allow generating without template_id (uses default).
        """
        data = {}
        serializer = ContractGenerateSerializer(data=data)
        assert serializer.is_valid()


class TestContractSignSerializer:
    """
    Tests for ContractSignSerializer.
    """

    def test_valid_sign_request(self):
        """
        Should validate sign request with name.
        """
        data = {
            'signed_by': 'John Doe',
        }
        serializer = ContractSignSerializer(data=data)
        assert serializer.is_valid()

    def test_sign_requires_name(self):
        """
        Should require signed_by field.
        """
        data = {}
        serializer = ContractSignSerializer(data=data)
        assert not serializer.is_valid()
        assert 'signed_by' in serializer.errors
