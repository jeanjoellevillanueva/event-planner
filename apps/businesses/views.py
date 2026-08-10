"""
Views for businesses app.
"""

from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import BusinessMembership
from apps.businesses.models import Business
from apps.businesses.serializers import BusinessCreateSerializer
from apps.businesses.serializers import BusinessDashboardSerializer
from apps.businesses.serializers import BusinessSerializer
from apps.common.permissions import IsBusinessAdmin
from apps.common.permissions import IsBusinessMember
from apps.common.permissions import IsBusinessOwner


class BusinessListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create businesses.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method == 'POST':
            return BusinessCreateSerializer
        return BusinessSerializer

    def get_queryset(self):
        """
        Return businesses the user belongs to.
        """
        return Business.objects.filter(
            memberships__user=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        """
        Create business and add user as owner.
        """
        business = serializer.save()

        BusinessMembership.objects.create(
            user=self.request.user,
            business=business,
            role='owner'
        )

        if not self.request.user.current_business:
            self.request.user.current_business = business
            self.request.user.save(update_fields=['current_business'])


class BusinessDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for business detail operations.
    """

    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated, IsBusinessMember]

    def get_queryset(self):
        """
        Return businesses the user belongs to.
        """
        return Business.objects.filter(
            memberships__user=self.request.user
        ).distinct()

    def get_permissions(self):
        """
        Set permissions based on request method.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), IsBusinessAdmin()]
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsBusinessOwner()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        """
        Delete business and clear current_business for affected users.
        """
        business = self.get_object()

        from django.contrib.auth import get_user_model
        User = get_user_model()

        User.objects.filter(current_business=business).update(current_business=None)

        return super().destroy(request, *args, **kwargs)


class BusinessDashboardView(APIView):
    """
    API endpoint for business dashboard stats.
    """

    permission_classes = [IsAuthenticated, IsBusinessMember]

    def get(self, request, pk):
        """
        Get dashboard statistics for a business.
        """
        try:
            business = Business.objects.get(
                pk=pk,
                memberships__user=request.user
            )
        except Business.DoesNotExist:
            return Response(
                {'error': 'Business not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        stats = business.get_dashboard_stats()
        serializer = BusinessDashboardSerializer(stats)
        return Response(serializer.data)
