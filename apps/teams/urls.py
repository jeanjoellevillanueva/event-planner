"""
URLs for teams app.
"""

from django.urls import path

from apps.teams.views import BookingAssignmentCreateView
from apps.teams.views import BookingAssignmentDeleteView
from apps.teams.views import BookingAssignmentListView
from apps.teams.views import TeamMemberDetailView
from apps.teams.views import TeamMemberListCreateView
from apps.teams.views import TeamMemberScheduleView

urlpatterns = [
    path('', TeamMemberListCreateView.as_view(), name='team_list_create'),
    path('<int:pk>/', TeamMemberDetailView.as_view(), name='team_detail'),
    path('<int:pk>/schedule/', TeamMemberScheduleView.as_view(), name='team_schedule'),
    path('assignments/<int:booking_id>/', BookingAssignmentListView.as_view(), name='assignment_list'),
    path('assignments/<int:booking_id>/assign/', BookingAssignmentCreateView.as_view(), name='assignment_create'),
    path('assignments/<int:booking_id>/<int:pk>/', BookingAssignmentDeleteView.as_view(), name='assignment_delete'),
]
