"""
User and membership models for Event Planner project.
"""

import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from apps.common.timezone import TIMEZONE_CHOICES


class User(AbstractUser):
    """
    Custom user model with timezone support and business context.
    """

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        choices=TIMEZONE_CHOICES,
    )
    current_business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_users',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def get_businesses(self):
        """
        Get all businesses the user belongs to.
        """
        return [m.business for m in self.business_memberships.select_related('business')]

    def get_role_for_business(self, business):
        """
        Get user's role for a specific business.
        """
        membership = self.business_memberships.filter(business=business).first()
        return membership.role if membership else None


class BusinessMembership(models.Model):
    """
    Pivot table linking users to businesses with roles.
    """

    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='business_memberships',
    )
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    permissions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'business']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.business.name} ({self.role})"


class Invitation(models.Model):
    """
    Email invitation for joining a business.
    """

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='invitations',
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation to {self.email} for {self.business.name}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=settings.INVITATION_EXPIRY_DAYS)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """
        Check if invitation has expired.
        """
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        """
        Check if invitation is valid and can be accepted.
        """
        return self.status == 'pending' and not self.is_expired
