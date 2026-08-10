"""
URLs for reminders app.
"""

from django.urls import path

from apps.reminders.views import ReminderCancelView
from apps.reminders.views import ReminderDetailView
from apps.reminders.views import ReminderListCreateView
from apps.reminders.views import ReminderSendNowView
from apps.reminders.views import ReminderTemplateDetailView
from apps.reminders.views import ReminderTemplateListCreateView

urlpatterns = [
    path('', ReminderListCreateView.as_view(), name='reminder_list_create'),
    path('<int:pk>/', ReminderDetailView.as_view(), name='reminder_detail'),
    path('<int:pk>/send-now/', ReminderSendNowView.as_view(), name='reminder_send_now'),
    path('<int:pk>/cancel/', ReminderCancelView.as_view(), name='reminder_cancel'),
    path('templates/', ReminderTemplateListCreateView.as_view(), name='template_list_create'),
    path('templates/<int:pk>/', ReminderTemplateDetailView.as_view(), name='template_detail'),
]
