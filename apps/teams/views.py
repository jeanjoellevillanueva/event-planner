"""
Views for teams app.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from apps.common.mixins import BusinessScopedMixin
from apps.common.permissions import IsBusinessAdmin
from apps.common.permissions import IsBusinessAdminOrReadOnly
from apps.common.permissions import IsBusinessMember
from apps.teams.models import BookingAssignment
from apps.teams.models import TeamMember
from apps.teams.serializers import BookingAssignmentCreateSerializer
from apps.teams.serializers import BookingAssignmentSerializer
from apps.teams.serializers import TeamMemberCreateSerializer
from apps.teams.serializers import TeamMemberListSerializer
from apps.teams.serializers import TeamMemberSerializer


class TeamMemberListCreateView(BusinessScopedMixin, generics.ListCreateAPIView):
    """
    API endpoint to list and create team members.
    """

    queryset = TeamMember.objects.select_related('user')
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'role']
    search_fields = ['name', 'email', 'role']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method == 'POST':
            return TeamMemberCreateSerializer
        if self.request.query_params.get('list', '').lower() == 'true':
            return TeamMemberListSerializer
        return TeamMemberSerializer


class TeamMemberDetailView(BusinessScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for team member detail operations.
    """

    queryset = TeamMember.objects.select_related('user')
    permission_classes = [IsAuthenticated, IsBusinessAdminOrReadOnly]

    def get_serializer_class(self):
        """
        Return appropriate serializer.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return TeamMemberCreateSerializer
        return TeamMemberSerializer


class BookingAssignmentListView(generics.ListAPIView):
    """
    API endpoint to list booking assignments for a booking.
    """

    serializer_class = BookingAssignmentSerializer
    permission_classes = [IsAuthenticated, IsBusinessMember]

    def get_queryset(self):
        """
        Return assignments for the specified booking.
        """
        booking_id = self.kwargs.get('booking_id')
        return BookingAssignment.objects.filter(
            booking_id=booking_id,
            booking__business=self.request.user.current_business
        ).select_related('team_member', 'assigned_by')


class BookingAssignmentCreateView(APIView):
    """
    API endpoint to assign team members to a booking.
    """

    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def post(self, request, booking_id):
        """
        Assign team member to a booking.
        """
        try:
            booking = Booking.objects.get(
                pk=booking_id,
                business=request.user.current_business
            )
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BookingAssignmentCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        existing = BookingAssignment.objects.filter(
            booking=booking,
            team_member=serializer.validated_data['team_member']
        ).exists()

        if existing:
            return Response(
                {'error': 'Team member is already assigned to this booking'},
                status=status.HTTP_400_BAD_REQUEST
            )

        assignment = BookingAssignment.objects.create(
            booking=booking,
            assigned_by=request.user,
            **serializer.validated_data
        )

        return Response({
            'message': 'Team member assigned successfully',
            'assignment': BookingAssignmentSerializer(assignment).data
        }, status=status.HTTP_201_CREATED)


class BookingAssignmentDeleteView(APIView):
    """
    API endpoint to remove team member from a booking.
    """

    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def delete(self, request, booking_id, pk):
        """
        Remove team member from a booking.
        """
        try:
            assignment = BookingAssignment.objects.get(
                pk=pk,
                booking_id=booking_id,
                booking__business=request.user.current_business
            )
        except BookingAssignment.DoesNotExist:
            return Response(
                {'error': 'Assignment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        assignment.delete()

        return Response(
            {'message': 'Assignment removed successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


class TeamMemberScheduleView(APIView):
    """
    API endpoint to get team member's schedule.
    """

    permission_classes = [IsAuthenticated, IsBusinessMember]

    def get(self, request, pk):
        """
        Get team member's assigned bookings.
        """
        try:
            team_member = TeamMember.objects.get(
                pk=pk,
                business=request.user.current_business
            )
        except TeamMember.DoesNotExist:
            return Response(
                {'error': 'Team member not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        assignments = team_member.booking_assignments.select_related(
            'booking', 'booking__client'
        ).order_by('booking__event_date')

        if from_date:
            assignments = assignments.filter(booking__event_date__gte=from_date)
        if to_date:
            assignments = assignments.filter(booking__event_date__lte=to_date)

        schedule = []
        for assignment in assignments:
            booking = assignment.booking
            schedule.append({
                'assignment_id': assignment.id,
                'booking_id': booking.id,
                'event_date': booking.event_date,
                'event_time': booking.event_time,
                'client_name': booking.client.name,
                'venue': booking.venue,
                'role': assignment.role or team_member.role,
                'status': booking.status
            })

        return Response({
            'team_member': TeamMemberSerializer(team_member).data,
            'schedule': schedule
        })
