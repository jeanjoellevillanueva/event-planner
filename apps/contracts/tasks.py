"""
Celery tasks for contracts app.
"""

import io
from celery import shared_task
from django.core.files.base import ContentFile


@shared_task
def generate_contract_pdf(contract_id):
    """
    Generate PDF from contract HTML content.

    Note: Requires weasyprint to be installed.
    In production, this generates PDF and uploads to DigitalOcean Spaces.
    """
    from apps.contracts.models import Contract

    try:
        contract = Contract.objects.select_related(
            'booking', 'booking__client', 'booking__business', 'template'
        ).get(pk=contract_id)
    except Contract.DoesNotExist:
        return f"Contract {contract_id} not found"

    if not contract.rendered_content:
        contract.render_content()
        contract.save(update_fields=['rendered_content'])

    try:
        from weasyprint import HTML

        html = HTML(string=contract.rendered_content)
        pdf_buffer = io.BytesIO()
        html.write_pdf(pdf_buffer)

        pdf_buffer.seek(0)
        filename = f"contract_{contract.id}_{contract.booking.id}.pdf"

        contract.generated_file.save(
            filename,
            ContentFile(pdf_buffer.read()),
            save=True
        )

        return f"PDF generated for contract {contract_id}"

    except ImportError:
        return f"weasyprint not installed. Contract {contract_id} content rendered but PDF not generated."
    except Exception as exc:
        return f"Error generating PDF for contract {contract_id}: {exc}"
