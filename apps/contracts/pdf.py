"""
WeasyPrint helpers for contract PDFs.
"""

import io

from django.core.files.base import ContentFile


def render_html_to_pdf_bytes(html_content):
    """
    Render HTML to PDF bytes with WeasyPrint.
    """
    from weasyprint import HTML

    buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(buffer)
    return buffer.getvalue()


def attach_generated_pdf(contract):
    """
    Build a PDF for a contract and store it on generated_file.
    """
    if not contract.rendered_content:
        contract.render_content()
        contract.save(update_fields=['rendered_content'])

    pdf_bytes = render_html_to_pdf_bytes(contract.rendered_content)
    filename = f"contract_{contract.id}_{contract.booking_id}.pdf"
    contract.generated_file.save(filename, ContentFile(pdf_bytes), save=True)
    return filename


def queue_contract_pdf(contract_id):
    """
    Enqueue PDF generation for a contract.
    """
    from apps.contracts.tasks import generate_contract_pdf

    generate_contract_pdf.delay(contract_id)
