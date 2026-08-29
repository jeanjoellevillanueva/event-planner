"""
Session-authenticated views for the Tailwind web UI.
"""

import calendar
from datetime import date
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.models import BusinessMembership
from apps.accounts.models import Invitation
from apps.bookings.models import Booking
from apps.clients.models import Client
from apps.common.timezone import to_user_timezone
from apps.common.timezone import to_utc
from apps.contracts.models import Contract
from apps.contracts.models import ContractTemplate
from apps.products.models import Package
from apps.products.models import Product
from apps.reminders.models import Reminder
from apps.teams.models import TeamMember
from apps.web.decorators import admin_required
from apps.web.decorators import business_required
from apps.web.decorators import safe_redirect_path
from apps.web.forms import BookingForm
from apps.web.forms import BusinessForm
from apps.web.forms import ClientForm
from apps.web.forms import ContractGenerateForm
from apps.web.forms import ContractTemplateForm
from apps.web.forms import InvitationRegisterForm
from apps.web.forms import InviteForm
from apps.web.forms import LoginForm
from apps.web.forms import PackageForm
from apps.web.forms import ProductForm
from apps.web.forms import RegisterForm
from apps.web.forms import ReminderForm
from apps.web.forms import RescheduleForm
from apps.web.forms import SwitchBusinessForm
from apps.web.forms import TeamMemberForm

User = get_user_model()


def home(request):
    """
    Send visitors to the dashboard or login page.
    """
    if request.user.is_authenticated:
        return redirect('web_dashboard')
    return redirect('web_login')


@require_http_methods(['GET', 'POST'])
def register(request):
    """
    Create an account with a timezone.
    """
    if request.user.is_authenticated:
        return redirect('web_dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            email=form.cleaned_data['email'],
            username=form.cleaned_data['username'],
            phone=form.cleaned_data.get('phone', ''),
            timezone=form.cleaned_data['timezone'],
            password=form.cleaned_data['password'],
        )
        login(request, user)
        messages.success(request, 'Welcome. Create your first business to get started.')
        return redirect('web_business_create')

    return render(request, 'web/register.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def login_view(request):
    """
    Log in with email and password.
    """
    if request.user.is_authenticated:
        return redirect('web_dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
        )
        if user is None:
            form.add_error(None, 'Invalid email or password.')
        else:
            login(request, user)
            return redirect(safe_redirect_path(request.GET.get('next')))

    return render(request, 'web/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    End the current session.
    """
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('web_login')


@login_required
@require_http_methods(['GET', 'POST'])
def business_create(request):
    """
    Create a business and make the user the owner.
    """
    form = BusinessForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        business = form.save()
        BusinessMembership.objects.create(
            user=request.user,
            business=business,
            role='owner',
        )
        request.user.current_business = business
        request.user.save(update_fields=['current_business'])
        messages.success(request, f'{business.name} is ready.')
        return redirect('web_dashboard')

    return render(request, 'web/business_form.html', {'form': form, 'title': 'Create business'})


@business_required
@require_http_methods(['GET', 'POST'])
def switch_business(request):
    """
    Switch the user's current store.
    """
    form = SwitchBusinessForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        business = form.cleaned_data['business']
        request.user.current_business = business
        request.user.save(update_fields=['current_business'])
        messages.success(request, f'Switched to {business.name}.')
        return redirect('web_dashboard')

    return render(request, 'web/switch_business.html', {'form': form})


@business_required
def dashboard(request):
    """
    Show store stats and upcoming events.
    """
    business = request.user.current_business
    stats = business.get_dashboard_stats()
    today = timezone.now().astimezone(ZoneInfo(request.user.timezone)).date()
    upcoming = business.bookings.filter(
        event_date__gte=today,
        status__in=['pending', 'confirmed'],
    ).select_related('client', 'package')[:8]
    return render(request, 'web/dashboard.html', {
        'stats': stats,
        'upcoming': upcoming,
    })


@business_required
def calendar_view(request):
    """
    Month calendar of bookings in the user's timezone context.
    """
    business = request.user.current_business
    today = timezone.now().astimezone(ZoneInfo(request.user.timezone)).date()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        date(year, month, 1)
    except (TypeError, ValueError):
        year, month = today.year, today.month

    month_start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    month_end = date(year, month, last_day)
    weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)

    bookings = list(
        business.bookings.filter(
            event_date__gte=weeks[0][0],
            event_date__lte=weeks[-1][-1],
        ).select_related('client', 'package')
    )
    by_day = {}
    for booking in bookings:
        by_day.setdefault(booking.event_date, []).append(booking)

    calendar_weeks = []
    for week in weeks:
        days = []
        for day in week:
            days.append({
                'date': day,
                'bookings': by_day.get(day, []),
                'in_month': day.month == month,
                'is_today': day == today,
            })
        calendar_weeks.append(days)

    if month == 1:
        prev_year, prev_month_num = year - 1, 12
    else:
        prev_year, prev_month_num = year, month - 1
    if month == 12:
        next_year, next_month_num = year + 1, 1
    else:
        next_year, next_month_num = year, month + 1

    return render(request, 'web/calendar.html', {
        'year': year,
        'month': month,
        'month_name': month_start.strftime('%B %Y'),
        'calendar_weeks': calendar_weeks,
        'today': today,
        'month_start': month_start,
        'month_end': month_end,
        'prev_year': prev_year,
        'prev_month': prev_month_num,
        'next_year': next_year,
        'next_month': next_month_num,
        'user_timezone': request.user.timezone,
    })


@business_required
def client_list(request):
    """
    List clients for the current store.
    """
    clients = request.user.current_business.clients.all()
    return render(request, 'web/clients/list.html', {'clients': clients})


@business_required
@require_http_methods(['GET', 'POST'])
def client_create(request):
    """
    Add a client to the current store.
    """
    form = ClientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        client = form.save(commit=False)
        client.business = request.user.current_business
        client.save()
        messages.success(request, f'{client.name} added.')
        return redirect('web_client_list')
    return render(request, 'web/clients/form.html', {'form': form, 'title': 'Add client'})


@admin_required
@require_http_methods(['GET', 'POST'])
def client_edit(request, pk):
    """
    Update a client in the current store.
    """
    client = get_object_or_404(Client, pk=pk, business=request.user.current_business)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{client.name} updated.')
        return redirect('web_client_list')
    return render(request, 'web/clients/form.html', {'form': form, 'title': 'Edit client'})


@business_required
def product_list(request):
    """
    List products for the current store.
    """
    products = request.user.current_business.products.all()
    return render(request, 'web/products/list.html', {'products': products})


@admin_required
@require_http_methods(['GET', 'POST'])
def product_create(request):
    """
    Add a product to the current store.
    """
    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        product.business = request.user.current_business
        product.save()
        messages.success(request, f'{product.name} added.')
        return redirect('web_product_list')
    return render(request, 'web/products/form.html', {'form': form, 'title': 'Add product'})


@admin_required
@require_http_methods(['GET', 'POST'])
def product_edit(request, pk):
    """
    Update a product in the current store.
    """
    product = get_object_or_404(Product, pk=pk, business=request.user.current_business)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{product.name} updated.')
        return redirect('web_product_list')
    return render(request, 'web/products/form.html', {'form': form, 'title': 'Edit product'})


@business_required
def package_list(request):
    """
    List packages for the current store.
    """
    packages = request.user.current_business.packages.all()
    return render(request, 'web/packages/list.html', {'packages': packages})


@admin_required
@require_http_methods(['GET', 'POST'])
def package_create(request):
    """
    Add a package to the current store.
    """
    form = PackageForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        package = form.save(commit=False)
        package.business = request.user.current_business
        package.save()
        messages.success(request, f'{package.name} added.')
        return redirect('web_package_list')
    return render(request, 'web/packages/form.html', {'form': form, 'title': 'Add package'})


@admin_required
@require_http_methods(['GET', 'POST'])
def package_edit(request, pk):
    """
    Update a package in the current store.
    """
    package = get_object_or_404(Package, pk=pk, business=request.user.current_business)
    form = PackageForm(request.POST or None, instance=package)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{package.name} updated.')
        return redirect('web_package_list')
    return render(request, 'web/packages/form.html', {'form': form, 'title': 'Edit package'})


@business_required
def booking_list(request):
    """
    List bookings for the current store.
    """
    bookings = request.user.current_business.bookings.select_related('client', 'package')
    return render(request, 'web/bookings/list.html', {'bookings': bookings})


@business_required
@require_http_methods(['GET', 'POST'])
def booking_create(request):
    """
    Create a booking for the current store.
    """
    business = request.user.current_business
    form = BookingForm(request.POST or None, business=business)
    if request.method == 'POST' and form.is_valid():
        booking = form.save(commit=False)
        booking.business = business
        booking.created_by = request.user
        if booking.package and not form.cleaned_data.get('total_amount'):
            booking.total_amount = booking.package.calculate_price(booking.pax_count)
        booking.save()
        messages.success(request, 'Booking created.')
        return redirect('web_booking_detail', pk=booking.pk)
    return render(request, 'web/bookings/form.html', {'form': form, 'title': 'New booking'})


@business_required
def booking_detail(request, pk):
    """
    Show booking detail, reschedule, and related records.
    """
    booking = get_object_or_404(
        Booking.objects.select_related('client', 'package'),
        pk=pk,
        business=request.user.current_business,
    )
    return render(request, 'web/bookings/detail.html', {
        'booking': booking,
        'reschedule_form': RescheduleForm(),
        'assignments': booking.team_assignments.select_related('team_member'),
        'contracts': booking.contracts.all(),
        'reminders': booking.reminders.all(),
    })


@business_required
@require_http_methods(['POST'])
def booking_reschedule(request, pk):
    """
    Reschedule a pending or confirmed booking.
    """
    booking = get_object_or_404(Booking, pk=pk, business=request.user.current_business)
    form = RescheduleForm(request.POST)
    if not booking.can_reschedule():
        messages.error(request, 'This booking cannot be rescheduled.')
        return redirect('web_booking_detail', pk=pk)
    if form.is_valid():
        booking.reschedule(
            new_date=form.cleaned_data['new_date'],
            new_time=form.cleaned_data.get('new_time'),
            reason=form.cleaned_data.get('reason', ''),
            approved_by=request.user,
        )
        messages.success(request, 'Booking rescheduled.')
    else:
        messages.error(request, 'Check the reschedule form and try again.')
    return redirect('web_booking_detail', pk=pk)


@business_required
def contract_list(request):
    """
    List contracts for the current store.
    """
    contracts = Contract.objects.filter(
        booking__business=request.user.current_business
    ).select_related('booking', 'booking__client', 'template')
    return render(request, 'web/contracts/list.html', {'contracts': contracts})


@admin_required
@require_http_methods(['GET', 'POST'])
def contract_generate(request):
    """
    Generate a contract from a template.
    """
    business = request.user.current_business
    form = ContractGenerateForm(request.POST or None, business=business)
    if request.method == 'POST' and form.is_valid():
        template = form.cleaned_data.get('template')
        if template is None:
            template = ContractTemplate.objects.filter(
                business=business,
                is_default=True,
                is_active=True,
            ).first()
        if template is None:
            form.add_error('template', 'Select a template or mark one as default.')
        else:
            contract = Contract.objects.create(
                booking=form.cleaned_data['booking'],
                template=template,
                generated_by=request.user,
                notes=form.cleaned_data.get('notes', ''),
                status='generated',
            )
            contract.render_content()
            contract.save(update_fields=['rendered_content'])
            messages.success(request, 'Contract generated.')
            return redirect('web_contract_detail', pk=contract.pk)
    return render(request, 'web/contracts/generate.html', {'form': form})


@business_required
def contract_detail(request, pk):
    """
    Show rendered contract content.
    """
    contract = get_object_or_404(
        Contract,
        pk=pk,
        booking__business=request.user.current_business,
    )
    return render(request, 'web/contracts/detail.html', {'contract': contract})


@admin_required
@require_http_methods(['GET', 'POST'])
def contract_template_create(request):
    """
    Create a contract template.
    """
    form = ContractTemplateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        template = form.save(commit=False)
        template.business = request.user.current_business
        template.save()
        messages.success(request, 'Template saved.')
        return redirect('web_contract_list')
    return render(request, 'web/contracts/template_form.html', {'form': form})


@business_required
def team_list(request):
    """
    List team members for the current store.
    """
    members = request.user.current_business.teammembers.all()
    return render(request, 'web/team/list.html', {'members': members})


@admin_required
@require_http_methods(['GET', 'POST'])
def team_create(request):
    """
    Add a team member to the current store.
    """
    form = TeamMemberForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        member = form.save(commit=False)
        member.business = request.user.current_business
        member.save()
        messages.success(request, f'{member.name} added.')
        return redirect('web_team_list')
    return render(request, 'web/team/form.html', {'form': form, 'title': 'Add team member'})


@business_required
def reminder_list(request):
    """
    List reminders for the current store.
    """
    reminders = list(
        Reminder.objects.filter(
            booking__business=request.user.current_business
        ).select_related('booking', 'booking__client')
    )
    for reminder in reminders:
        reminder.scheduled_display = to_user_timezone(
            reminder.scheduled_at,
            request.user.timezone,
        )
    return render(request, 'web/reminders/list.html', {'reminders': reminders})


@business_required
@require_http_methods(['GET', 'POST'])
def reminder_create(request):
    """
    Schedule a reminder stored in UTC.
    """
    business = request.user.current_business
    form = ReminderForm(request.POST or None, business=business)
    if request.method == 'POST' and form.is_valid():
        reminder = form.save(commit=False)
        scheduled = reminder.scheduled_at
        if timezone.is_aware(scheduled):
            scheduled = scheduled.replace(tzinfo=None)
        reminder.scheduled_at = to_utc(scheduled, request.user.timezone)
        reminder.save()
        messages.success(request, 'Reminder scheduled.')
        return redirect('web_reminder_list')
    return render(request, 'web/reminders/form.html', {'form': form})


@admin_required
@require_http_methods(['GET', 'POST'])
def invite_create(request):
    """
    Invite a teammate by email.
    """
    form = InviteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        invitation = Invitation.objects.create(
            business=request.user.current_business,
            email=form.cleaned_data['email'],
            role=form.cleaned_data['role'],
            invited_by=request.user,
        )
        accept_url = f"{settings.FRONTEND_URL}/invitations/{invitation.token}/"
        messages.success(
            request,
            f'Invitation created for {invitation.email}. Share {accept_url}',
        )
        return redirect('web_invite_create')
    invitations = Invitation.objects.filter(business=request.user.current_business)
    return render(request, 'web/invites.html', {
        'form': form,
        'invitations': invitations,
    })


@require_http_methods(['GET', 'POST'])
def invitation_accept(request, token):
    """
    Accept an invitation or register through it.
    """
    invitation = get_object_or_404(Invitation, token=token)
    if invitation.is_expired:
        invitation.status = 'expired'
        invitation.save(update_fields=['status'])
        messages.error(request, 'This invitation has expired.')
        return redirect('web_login')
    if invitation.status != 'pending':
        messages.error(request, 'This invitation is no longer valid.')
        return redirect('web_login')

    if request.user.is_authenticated:
        if request.user.email != invitation.email:
            messages.error(request, 'Sign in with the invited email to accept.')
            return redirect('web_dashboard')
        if BusinessMembership.objects.filter(
            user=request.user,
            business=invitation.business,
        ).exists():
            messages.error(request, 'You are already a member of this business.')
            return redirect('web_dashboard')
        if request.method == 'POST':
            accept_invitation_for_user(request.user, invitation)
            messages.success(request, f'You joined {invitation.business.name}.')
            return redirect('web_dashboard')
        return render(request, 'web/invitation_accept.html', {
            'invitation': invitation,
            'form': None,
        })

    existing = User.objects.filter(email=invitation.email).exists()
    form = InvitationRegisterForm(
        request.POST or None,
        initial={'email': invitation.email},
    )
    if existing:
        messages.info(request, 'Log in with the invited email to accept.')
        return redirect('web_login')

    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            email=invitation.email,
            username=form.cleaned_data['username'],
            phone=form.cleaned_data.get('phone', ''),
            timezone=form.cleaned_data['timezone'],
            password=form.cleaned_data['password'],
        )
        accept_invitation_for_user(user, invitation)
        login(request, user)
        messages.success(request, f'Welcome to {invitation.business.name}.')
        return redirect('web_dashboard')

    return render(request, 'web/invitation_accept.html', {
        'invitation': invitation,
        'form': form,
    })


def accept_invitation_for_user(user, invitation):
    """
    Attach a user to the invited business and mark the invite accepted.
    """
    BusinessMembership.objects.create(
        user=user,
        business=invitation.business,
        role=invitation.role,
    )
    invitation.status = 'accepted'
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=['status', 'accepted_at'])
    if not user.current_business:
        user.current_business = invitation.business
        user.save(update_fields=['current_business'])
