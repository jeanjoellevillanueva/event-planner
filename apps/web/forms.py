"""
Forms for the Tailwind web UI.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from apps.bookings.models import Booking
from apps.businesses.models import Business
from apps.clients.models import Client
from apps.common.timezone import COMMON_TIMEZONE_CHOICES
from apps.common.timezone import is_valid_timezone
from apps.contracts.models import ContractTemplate
from apps.products.models import Package
from apps.products.models import Product
from apps.reminders.models import Reminder
from apps.teams.models import TeamMember

User = get_user_model()


class StyledFormMixin:
    """
    Apply shared input classes to form widgets.
    """

    def apply_input_classes(self):
        """
        Add Tailwind input classes to visible fields.
        """
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{css} input'.strip()


class RegisterForm(StyledFormMixin, forms.Form):
    """
    Email and timezone registration form.
    """

    email = forms.EmailField()
    username = forms.CharField(max_length=150)
    phone = forms.CharField(max_length=20, required=False)
    timezone = forms.ChoiceField(choices=COMMON_TIMEZONE_CHOICES, initial='UTC')
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()

    def clean_email(self):
        """
        Reject emails that already have an account.
        """
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_timezone(self):
        """
        Require a valid IANA timezone.
        """
        value = self.cleaned_data['timezone']
        if not is_valid_timezone(value):
            raise forms.ValidationError('Invalid timezone.')
        return value

    def clean(self):
        """
        Ensure passwords match and pass Django validators.
        """
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('password_confirm')
        if password and confirm and password != confirm:
            self.add_error('password_confirm', 'Passwords do not match.')
        if password:
            validate_password(password)
        return cleaned


class LoginForm(StyledFormMixin, forms.Form):
    """
    Email and password login form.
    """

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()


class BusinessForm(StyledFormMixin, forms.ModelForm):
    """
    Create or update a business store.
    """

    class Meta:
        model = Business
        fields = [
            'name', 'business_type', 'email', 'phone', 'address',
            'website', 'description',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()


class ClientForm(StyledFormMixin, forms.ModelForm):
    """
    Create or update a client.
    """

    class Meta:
        model = Client
        fields = [
            'name', 'email', 'phone', 'secondary_phone',
            'address', 'city', 'notes', 'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()


class ProductForm(StyledFormMixin, forms.ModelForm):
    """
    Create or update a product.
    """

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'base_price',
            'unit', 'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()


class PackageForm(StyledFormMixin, forms.ModelForm):
    """
    Create or update a package.
    """

    class Meta:
        model = Package
        fields = [
            'name', 'description', 'base_price', 'min_pax', 'max_pax',
            'price_per_additional_pax', 'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()


class BookingForm(StyledFormMixin, forms.ModelForm):
    """
    Create or update a booking.
    """

    class Meta:
        model = Booking
        fields = [
            'client', 'package', 'event_date', 'event_time', 'event_end_time',
            'venue', 'venue_address', 'pax_count', 'status',
            'total_amount', 'deposit_amount', 'notes', 'special_requests',
        ]
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'event_time': forms.TimeInput(attrs={'type': 'time'}),
            'event_end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()
        if business is not None:
            self.fields['client'].queryset = Client.objects.filter(business=business)
            self.fields['package'].queryset = Package.objects.filter(business=business)
            self.fields['package'].required = False


class RescheduleForm(StyledFormMixin, forms.Form):
    """
    Reschedule an existing booking.
    """

    new_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    new_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}))
    reason = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()


class TeamMemberForm(StyledFormMixin, forms.ModelForm):
    """
    Create or update a team member.
    """

    class Meta:
        model = TeamMember
        fields = ['name', 'email', 'phone', 'role', 'hourly_rate', 'notes', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()


class ReminderForm(StyledFormMixin, forms.ModelForm):
    """
    Schedule a reminder for a booking.
    """

    class Meta:
        model = Reminder
        fields = [
            'booking', 'reminder_type', 'scheduled_at',
            'subject', 'message', 'recipient_email', 'recipient_phone',
        ]
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()
        if business is not None:
            self.fields['booking'].queryset = Booking.objects.filter(business=business)


class ContractTemplateForm(StyledFormMixin, forms.ModelForm):
    """
    Create or update a contract template.
    """

    class Meta:
        model = ContractTemplate
        fields = ['name', 'description', 'content', 'is_default', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 12}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()


class ContractGenerateForm(StyledFormMixin, forms.Form):
    """
    Generate a contract from a template.
    """

    booking = forms.ModelChoiceField(queryset=Booking.objects.none())
    template = forms.ModelChoiceField(queryset=ContractTemplate.objects.none(), required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()
        if business is not None:
            self.fields['booking'].queryset = Booking.objects.filter(business=business)
            self.fields['template'].queryset = ContractTemplate.objects.filter(
                business=business,
                is_active=True,
            )


class InviteForm(StyledFormMixin, forms.Form):
    """
    Invite a teammate by email.
    """

    email = forms.EmailField()
    role = forms.ChoiceField(choices=[('admin', 'Admin'), ('staff', 'Staff')])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()


class InvitationRegisterForm(RegisterForm):
    """
    Registration form used when accepting an invite.
    """

    email = forms.EmailField(disabled=True, required=False)


class SwitchBusinessForm(StyledFormMixin, forms.Form):
    """
    Switch the user's current store.
    """

    business = forms.ModelChoiceField(queryset=Business.objects.none())

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_classes()
        if user is not None:
            self.fields['business'].queryset = Business.objects.filter(
                memberships__user=user
            ).distinct()
