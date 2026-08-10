"""
Invitation URLs for accounts app.
"""

from django.urls import path

from apps.accounts.views import InvitationAcceptView
from apps.accounts.views import InvitationDetailView
from apps.accounts.views import InvitationListCreateView
from apps.accounts.views import InvitationRegisterView

urlpatterns = [
    path('', InvitationListCreateView.as_view(), name='invitation_list_create'),
    path('<uuid:token>/', InvitationDetailView.as_view(), name='invitation_detail'),
    path('<uuid:token>/accept/', InvitationAcceptView.as_view(), name='invitation_accept'),
    path('<uuid:token>/register/', InvitationRegisterView.as_view(), name='invitation_register'),
]
