"""
Tests for WeasyPrint contract PDF generation.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from apps.contracts.models import Contract
from apps.contracts.models import ContractTemplate
from apps.contracts.pdf import attach_generated_pdf
from apps.contracts.tasks import generate_contract_pdf


@pytest.mark.django_db
class TestContractPdf:
    """
    Tests for contract PDF rendering and the Celery task.
    """

    def create_contract(self, booking_factory, business_factory):
        """
        Build a generated contract with rendered HTML.
        """
        business = business_factory()
        booking = booking_factory(business=business)
        template = ContractTemplate.objects.create(
            business=business,
            name='Standard',
            content='<p>Hello {{client_name}}</p>',
            is_default=True,
        )
        contract = Contract.objects.create(
            booking=booking,
            template=template,
            status='generated',
        )
        contract.render_content()
        contract.save(update_fields=['rendered_content'])
        return contract

    @patch('apps.contracts.pdf.render_html_to_pdf_bytes', return_value=b'%PDF-test')
    def test_attach_generated_pdf_saves_file(
        self,
        mock_render,
        booking_factory,
        business_factory,
    ):
        """
        PDF bytes should be stored on the contract file field.
        """
        contract = self.create_contract(booking_factory, business_factory)
        filename = attach_generated_pdf(contract)
        contract.refresh_from_db()
        assert filename.endswith('.pdf')
        assert contract.generated_file
        mock_render.assert_called_once()

    @patch('apps.contracts.pdf.attach_generated_pdf', side_effect=ImportError)
    def test_generate_task_handles_missing_weasyprint(
        self,
        mock_attach,
        booking_factory,
        business_factory,
    ):
        """
        Missing WeasyPrint should not raise from the Celery task.
        """
        contract = self.create_contract(booking_factory, business_factory)
        result = generate_contract_pdf(contract.id)
        assert 'weasyprint not installed' in result

    def test_generate_task_reports_missing_contract(self):
        """
        Unknown contract ids should return a not-found message.
        """
        assert generate_contract_pdf(999999) == 'Contract 999999 not found'
