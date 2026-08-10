"""
Middleware for Event Planner project.
"""

from django.http import JsonResponse


class BusinessContextMiddleware:
    """
    Middleware to validate and inject business context for authenticated requests.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Process request and validate business context.
        """
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Validate business access before view execution.
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None

        if request.path.startswith('/admin/'):
            return None

        if request.path.startswith('/api/v1/auth/'):
            return None

        if request.path.startswith('/api/v1/users/me'):
            return None

        if request.path.startswith('/api/v1/invitations/'):
            return None

        if request.path == '/api/v1/businesses/' and request.method == 'GET':
            return None

        user = request.user
        current_business = getattr(user, 'current_business', None)

        if not current_business:
            if hasattr(user, 'business_memberships'):
                first_membership = user.business_memberships.first()
                if first_membership:
                    user.current_business = first_membership.business
                    user.save(update_fields=['current_business'])
                    return None

            if not self.is_business_creation_request(request):
                return JsonResponse(
                    {'error': 'No business selected. Please select or create a business.'},
                    status=400
                )

        return None

    def is_business_creation_request(self, request):
        """
        Check if request is for creating a new business.
        """
        return (
            request.method == 'POST' and
            request.path == '/api/v1/businesses/'
        )
