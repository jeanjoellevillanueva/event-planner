"""
Celery tasks for contracts app.
"""

from celery import shared_task


@shared_task
def generate_contract_pdf(contract_id):
    """
    Generate a PDF from contract HTML and store it on the contract.
    """
    from apps.contracts.models import Contract
    from apps.contracts.pdf import attach_generated_pdf

    try:
        contract = Contract.objects.select_related(
            'booking', 'booking__client', 'booking__business', 'template'
        ).get(pk=contract_id)
    except Contract.DoesNotExist:
        return f"Contract {contract_id} not found"

    try:
        attach_generated_pdf(contract)
        return f"PDF generated for contract {contract_id}"
    except ImportError:
        return (
            f"weasyprint not installed. Contract {contract_id} content "
            "rendered but PDF not generated."
        )
    except Exception as exc:
        return f"Error generating PDF for contract {contract_id}: {exc}"
