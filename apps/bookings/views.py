"""
Views for bookings app.
"""

from datetime import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from apps.bookings.serializers import BookingCreateSerializer
from apps.bookings.serializers import BookingListSerializer
from apps.bookings.serializers import BookingRescheduleRequestSerializer
from apps.bookings.serializers import BookingSerializer
from apps.bookings.serializers import CalendarEventSerializer
from apps.common.mixins import BusinessScopedMixin
from apps.common.permissions import IsBusinessAdminOrReadOnly
from apps.common.permissions import IsBusinessMember
from apps.common.timezone import is_valid_timezone


class BookingListCreateView(BusinessScopedMixin, generics.ListCreateAPIView):
    """
    API endpoint to list and create bookings.
    """

    queryset = Booking.objects.select_related('client', 'package', 'created_by')
    permission_classes = [IsAuthenticated, IsBusinessMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'client', 'package']
    search_fields = ['client__name', 'venue', 'notes']
    ordering_fields = ['event_date', 'created_at', 'total_amount']
    ordering = ['-event_date']

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method == 'POST':
            return BookingCreateSerializer
        if self.request.query_params.get('list', '').lower() == 'true':
            return BookingListSerializer
        return BookingSerializer

    def perform_create(self, serializer):
        """
        Set business and created_by on create.
        """
        serializer.save(
            business=self.request.user.current_business,
            created_by=self.request.user
        )


class BookingDetailView(BusinessScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for booking detail operations.
    """

    queryset = Booking.objects.select_related('client', 'package', 'created_by')
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return BookingCreateSerializer
        return BookingSerializer


class BookingRescheduleView(APIView):
    """
    API endpoint to reschedule a booking.
    """

    permission_classes = [IsAuthenticated, IsBusinessMember]

    def post(self, request, pk):
        """
        Reschedule a booking.
        """
        try:
            booking = Booking.objects.get(
                pk=pk,
                business=request.user.current_business
            )
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not booking.can_reschedule():
            return Response(
                {'error': 'Cannot reschedule a completed or cancelled booking'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BookingRescheduleRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking.reschedule(
            new_date=serializer.validated_data['new_date'],
            new_time=serializer.validated_data.get('new_time'),
            reason=serializer.validated_data.get('reason', ''),
            approved_by=request.user
        )

        return Response({
            'message': 'Booking rescheduled successfully',
            'booking': BookingSerializer(booking, context={'request': request}).data
        })


class BookingCalendarView(APIView):
    """
    API endpoint for calendar view of bookings.
    """

    permission_classes = [IsAuthenticated, IsBusinessMember]

    STATUS_COLORS = {
        'pending': '#FFA500',
        'confirmed': '#4CAF50',
        'completed': '#2196F3',
        'cancelled': '#F44336',
    }

    def get(self, request):
        """
        Get bookings as calendar events.
        """
        business = request.user.current_business

        tz_param = request.query_params.get('tz')
        if tz_param:
            if not is_valid_timezone(tz_param):
                return Response(
                    {'error': 'Invalid timezone parameter'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user_tz = ZoneInfo(tz_param)
        else:
            user_tz = ZoneInfo(request.user.timezone)

        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')

        bookings = Booking.objects.filter(business=business)

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                bookings = bookings.filter(event_date__gte=start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                bookings = bookings.filter(event_date__lte=end)
            except ValueError:
                pass

        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)

        bookings = bookings.select_related('client', 'package')

        events = []
        for booking in bookings:
            start_dt = datetime.combine(
                booking.event_date,
                booking.event_time or datetime.min.time()
            )
            start_dt = start_dt.replace(tzinfo=ZoneInfo('UTC'))
            start_dt = start_dt.astimezone(user_tz)

            end_dt = None
            if booking.event_end_time:
                end_dt = datetime.combine(
                    booking.event_date,
                    booking.event_end_time
                )
                end_dt = end_dt.replace(tzinfo=ZoneInfo('UTC'))
                end_dt = end_dt.astimezone(user_tz)

            event = {
                'id': booking.id,
                'title': f"{booking.client.name} - {booking.package.name if booking.package else 'Custom'}",
                'start': start_dt,
                'end': end_dt,
                'status': booking.status,
                'client_name': booking.client.name,
                'venue': booking.venue,
                'pax_count': booking.pax_count,
                'color': self.STATUS_COLORS.get(booking.status, '#9E9E9E')
            }
            events.append(event)

        serializer = CalendarEventSerializer(events, many=True)
        return Response(serializer.data)
