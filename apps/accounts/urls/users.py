"""
User URLs for accounts app.
"""

from django.urls import path

from apps.accounts.views import SwitchBusinessView
from apps.accounts.views import UserBusinessesView
from apps.accounts.views import UserProfileView

urlpatterns = [
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('me/businesses/', UserBusinessesView.as_view(), name='user_businesses'),
    path('me/switch-business/', SwitchBusinessView.as_view(), name='switch_business'),
]
