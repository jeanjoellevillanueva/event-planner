"""
URLs for bookings app.
"""

from django.urls import path

from apps.bookings.views import BookingCalendarView
from apps.bookings.views import BookingDetailView
from apps.bookings.views import BookingListCreateView
from apps.bookings.views import BookingRescheduleView

urlpatterns = [
    path('', BookingListCreateView.as_view(), name='booking_list_create'),
    path('calendar/', BookingCalendarView.as_view(), name='booking_calendar'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/reschedule/', BookingRescheduleView.as_view(), name='booking_reschedule'),
]
