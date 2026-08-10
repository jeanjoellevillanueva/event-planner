"""
Serializer mixins for Event Planner project.
"""

from rest_framework import serializers

from apps.common.timezone import to_user_timezone


class TimezoneAwareMixin:
    """
    Mixin to convert datetime fields to user's timezone in API responses.
    """

    def to_representation(self, instance):
        """
        Convert all DateTimeField values to user's timezone.
        """
        data = super().to_representation(instance)
        request = self.context.get('request')

        if not request:
            return data

        user_tz = self.get_user_timezone(request)
        if not user_tz:
            return data

        for field_name, field in self.fields.items():
            if isinstance(field, serializers.DateTimeField) and data.get(field_name):
                dt = getattr(instance, field_name, None)
                if dt:
                    data[field_name] = to_user_timezone(dt, user_tz).isoformat()

        return data

    def get_user_timezone(self, request):
        """
        Get timezone from request query param or user profile.
        """
        if hasattr(request, 'query_params'):
            tz_param = request.query_params.get('tz')
            if tz_param:
                return tz_param

        if hasattr(request, 'user') and request.user.is_authenticated:
            return getattr(request.user, 'timezone', 'UTC')

        return 'UTC'


class BusinessScopedMixin:
    """
    Mixin to automatically scope querysets to current business.
    """

    def get_queryset(self):
        """
        Filter queryset by current business.
        """
        queryset = super().get_queryset()
        request = self.request

        if hasattr(request, 'user') and request.user.is_authenticated:
            current_business = getattr(request.user, 'current_business', None)
            if current_business:
                queryset = queryset.filter(business=current_business)

        return queryset

    def perform_create(self, serializer):
        """
        Set business on create.
        """
        serializer.save(business=self.request.user.current_business)
