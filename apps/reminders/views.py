"""
Views for reminders app.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import BusinessScopedMixin
from apps.common.permissions import IsBusinessAdmin
from apps.common.permissions import IsBusinessAdminOrReadOnly
from apps.common.permissions import IsBusinessMember
from apps.reminders.models import Reminder
from apps.reminders.models import ReminderTemplate
from apps.reminders.serializers import ReminderCreateSerializer
from apps.reminders.serializers import ReminderSerializer
from apps.reminders.serializers import ReminderTemplateCreateSerializer
from apps.reminders.serializers import ReminderTemplateSerializer
from apps.reminders.tasks import send_reminder


class ReminderListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create reminders.
    """

    permission_classes = [IsAuthenticated, IsBusinessMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'reminder_type']
    ordering_fields = ['scheduled_at', 'created_at']
    ordering = ['scheduled_at']

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method == 'POST':
            return ReminderCreateSerializer
        return ReminderSerializer

    def get_queryset(self):
        """
        Return reminders for current business.
        """
        return Reminder.objects.filter(
            booking__business=self.request.user.current_business
        ).select_related('booking', 'booking__client')


class ReminderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for reminder detail operations.
    """

    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]

    def get_queryset(self):
        """
        Return reminders for current business.
        """
        return Reminder.objects.filter(
            booking__business=self.request.user.current_business
        ).select_related('booking', 'booking__client')


class ReminderSendNowView(APIView):
    """
    API endpoint to send a reminder immediately.
    """

    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def post(self, request, pk):
        """
        Send reminder immediately.
        """
        try:
            reminder = Reminder.objects.get(
                pk=pk,
                booking__business=request.user.current_business
            )
        except Reminder.DoesNotExist:
            return Response(
                {'error': 'Reminder not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not reminder.can_send:
            return Response(
                {'error': f'Reminder cannot be sent (status: {reminder.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        send_reminder.delay(reminder.id)

        return Response({
            'message': 'Reminder queued for sending',
            'reminder_id': reminder.id
        })


class ReminderCancelView(APIView):
    """
    API endpoint to cancel a pending reminder.
    """

    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def post(self, request, pk):
        """
        Cancel a pending reminder.
        """
        try:
            reminder = Reminder.objects.get(
                pk=pk,
                booking__business=request.user.current_business
            )
        except Reminder.DoesNotExist:
            return Response(
                {'error': 'Reminder not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if reminder.status != 'pending':
            return Response(
                {'error': 'Only pending reminders can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reminder.status = 'cancelled'
        reminder.save(update_fields=['status', 'updated_at'])

        return Response({
            'message': 'Reminder cancelled',
            'reminder': ReminderSerializer(reminder).data
        })


class ReminderTemplateListCreateView(BusinessScopedMixin, generics.ListCreateAPIView):
    """
    API endpoint to list and create reminder templates.
    """

    queryset = ReminderTemplate.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'template_type']

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method == 'POST':
            return ReminderTemplateCreateSerializer
        return ReminderTemplateSerializer


class ReminderTemplateDetailView(BusinessScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for reminder template detail operations.
    """

    queryset = ReminderTemplate.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return ReminderTemplateCreateSerializer
        return ReminderTemplateSerializer
