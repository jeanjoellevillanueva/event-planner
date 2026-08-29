"""
Access helpers for web views.
"""

from functools import wraps
from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def safe_redirect_path(next_url, fallback='web_dashboard'):
    """
    Allow only same-origin relative paths for post-login redirects.
    """
    if not next_url:
        return fallback
    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc:
        return fallback
    if not next_url.startswith('/') or next_url.startswith('//'):
        return fallback
    return next_url


def business_required(view):
    """
    Require membership in the selected business before showing store pages.
    """

    @login_required
    @wraps(view)
    def wrapped_view(request, *args, **kwargs):
        """
        Redirect users who still need a store.
        """
        business = getattr(request.user, 'current_business', None)
        if not business or request.user.get_role_for_business(business) is None:
            if business:
                request.user.current_business = None
                request.user.save(update_fields=['current_business'])
            messages.info(request, 'Create or select a business to continue.')
            return redirect('web_business_create')
        return view(request, *args, **kwargs)

    return wrapped_view


def admin_required(view):
    """
    Require owner or admin role for the current business.
    """

    @business_required
    @wraps(view)
    def wrapped_view(request, *args, **kwargs):
        """
        Block staff from admin-only pages.
        """
        role = request.user.get_role_for_business(request.user.current_business)
        if role not in ('owner', 'admin'):
            messages.error(request, 'Admin access required.')
            return redirect('web_dashboard')
        return view(request, *args, **kwargs)

    return wrapped_view
