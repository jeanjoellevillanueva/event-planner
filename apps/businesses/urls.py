"""
URLs for businesses app.
"""

from django.urls import path

from apps.businesses.views import BusinessDashboardView
from apps.businesses.views import BusinessDetailView
from apps.businesses.views import BusinessListCreateView

urlpatterns = [
    path('', BusinessListCreateView.as_view(), name='business_list_create'),
    path('<int:pk>/', BusinessDetailView.as_view(), name='business_detail'),
    path('<int:pk>/dashboard/', BusinessDashboardView.as_view(), name='business_dashboard'),
]
