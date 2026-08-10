"""
URL configuration for Event Planner project.
"""

from django.contrib import admin
from django.urls import include
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls.auth')),
    path('api/v1/users/', include('apps.accounts.urls.users')),
    path('api/v1/invitations/', include('apps.accounts.urls.invitations')),
    path('api/v1/businesses/', include('apps.businesses.urls')),
    path('api/v1/clients/', include('apps.clients.urls')),
    path('api/v1/products/', include('apps.products.urls')),
    path('api/v1/bookings/', include('apps.bookings.urls')),
    path('api/v1/contracts/', include('apps.contracts.urls')),
    path('api/v1/team/', include('apps.teams.urls')),
    path('api/v1/reminders/', include('apps.reminders.urls')),
]
