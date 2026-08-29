"""
Template context for the web UI.
"""


def business_context(request):
    """
    Expose the current store and role to every template.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'current_business': None,
            'current_role': None,
            'user_businesses': [],
            'is_business_admin': False,
        }

    business = getattr(user, 'current_business', None)
    role = user.get_role_for_business(business) if business else None
    return {
        'current_business': business,
        'current_role': role,
        'user_businesses': user.get_businesses(),
        'is_business_admin': role in ('owner', 'admin'),
    }
