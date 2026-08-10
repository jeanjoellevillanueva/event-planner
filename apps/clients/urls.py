"""
URLs for clients app.
"""

from django.urls import path

from apps.clients.views import ClientDetailView
from apps.clients.views import ClientListCreateView

urlpatterns = [
    path('', ClientListCreateView.as_view(), name='client_list_create'),
    path('<int:pk>/', ClientDetailView.as_view(), name='client_detail'),
]
