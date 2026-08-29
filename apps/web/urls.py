"""
URL routes for the Tailwind web UI.
"""

from django.urls import path

from apps.web import views

urlpatterns = [
    path('', views.home, name='web_home'),
    path('register/', views.register, name='web_register'),
    path('login/', views.login_view, name='web_login'),
    path('logout/', views.logout_view, name='web_logout'),
    path('businesses/new/', views.business_create, name='web_business_create'),
    path('businesses/switch/', views.switch_business, name='web_switch_business'),
    path('dashboard/', views.dashboard, name='web_dashboard'),
    path('calendar/', views.calendar_view, name='web_calendar'),
    path('clients/', views.client_list, name='web_client_list'),
    path('clients/new/', views.client_create, name='web_client_create'),
    path('clients/<int:pk>/edit/', views.client_edit, name='web_client_edit'),
    path('products/', views.product_list, name='web_product_list'),
    path('products/new/', views.product_create, name='web_product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='web_product_edit'),
    path('packages/', views.package_list, name='web_package_list'),
    path('packages/new/', views.package_create, name='web_package_create'),
    path('packages/<int:pk>/edit/', views.package_edit, name='web_package_edit'),
    path('bookings/', views.booking_list, name='web_booking_list'),
    path('bookings/new/', views.booking_create, name='web_booking_create'),
    path('bookings/<int:pk>/', views.booking_detail, name='web_booking_detail'),
    path('bookings/<int:pk>/reschedule/', views.booking_reschedule, name='web_booking_reschedule'),
    path('contracts/', views.contract_list, name='web_contract_list'),
    path('contracts/new/', views.contract_generate, name='web_contract_generate'),
    path('contracts/templates/new/', views.contract_template_create, name='web_contract_template_create'),
    path('contracts/<int:pk>/', views.contract_detail, name='web_contract_detail'),
    path('team/', views.team_list, name='web_team_list'),
    path('team/new/', views.team_create, name='web_team_create'),
    path('reminders/', views.reminder_list, name='web_reminder_list'),
    path('reminders/new/', views.reminder_create, name='web_reminder_create'),
    path('invites/', views.invite_create, name='web_invite_create'),
    path('invitations/<uuid:token>/', views.invitation_accept, name='web_invitation_accept'),
]
