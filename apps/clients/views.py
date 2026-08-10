"""
Views for clients app.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.clients.models import Client
from apps.clients.serializers import ClientCreateSerializer
from apps.clients.serializers import ClientListSerializer
from apps.clients.serializers import ClientSerializer
from apps.common.mixins import BusinessScopedMixin
from apps.common.permissions import IsBusinessAdminOrReadOnly
from apps.common.permissions import IsBusinessMember


class ClientListCreateView(BusinessScopedMixin, generics.ListCreateAPIView):
    """
    API endpoint to list and create clients.
    """

    queryset = Client.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'city']
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method == 'POST':
            return ClientCreateSerializer
        if self.request.query_params.get('list', '').lower() == 'true':
            return ClientListSerializer
        return ClientSerializer


class ClientDetailView(BusinessScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for client detail operations.
    """

    queryset = Client.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return ClientCreateSerializer
        return ClientSerializer
