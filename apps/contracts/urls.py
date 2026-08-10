"""
URLs for contracts app.
"""

from django.urls import path

from apps.contracts.views import ContractDetailView
from apps.contracts.views import ContractDownloadView
from apps.contracts.views import ContractGenerateView
from apps.contracts.views import ContractListView
from apps.contracts.views import ContractSignView
from apps.contracts.views import ContractTemplateDetailView
from apps.contracts.views import ContractTemplateListCreateView

urlpatterns = [
    path('templates/', ContractTemplateListCreateView.as_view(), name='template_list_create'),
    path('templates/<int:pk>/', ContractTemplateDetailView.as_view(), name='template_detail'),
    path('', ContractListView.as_view(), name='contract_list'),
    path('<int:pk>/', ContractDetailView.as_view(), name='contract_detail'),
    path('<int:pk>/download/', ContractDownloadView.as_view(), name='contract_download'),
    path('<int:pk>/mark-signed/', ContractSignView.as_view(), name='contract_sign'),
    path('generate/<int:booking_id>/', ContractGenerateView.as_view(), name='contract_generate'),
]
