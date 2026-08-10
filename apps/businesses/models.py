"""
Business models for Event Planner project.
"""

from django.db import models
from django.utils.text import slugify

from apps.common.models import BaseModel


class Business(BaseModel):
    """
    Business/tenant model representing a company using the platform.
    """

    BUSINESS_TYPE_CHOICES = [
        ('event', 'Event Planning'),
        ('catering', 'Catering Services'),
        ('souvenirs', 'Souvenirs'),
        ('balloon', 'Balloon/Backdrop Services'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPE_CHOICES)
    logo = models.ImageField(upload_to='business_logos/', null=True, blank=True)
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    settings = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'businesses'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def generate_unique_slug(self):
        """
        Generate a unique slug for the business.
        """
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def get_dashboard_stats(self):
        """
        Get dashboard statistics for the business.
        """
        from django.db.models import Count
        from django.db.models import Sum
        from django.utils import timezone

        today = timezone.now().date()
        month_start = today.replace(day=1)

        stats = {
            'total_clients': self.clients.count(),
            'total_bookings': self.bookings.count(),
            'pending_bookings': self.bookings.filter(status='pending').count(),
            'confirmed_bookings': self.bookings.filter(status='confirmed').count(),
            'upcoming_events': self.bookings.filter(
                event_date__gte=today,
                status='confirmed'
            ).count(),
            'monthly_bookings': self.bookings.filter(
                created_at__date__gte=month_start
            ).count(),
            'total_products': self.products.count(),
            'total_packages': self.packages.count(),
            'team_members': self.memberships.count(),
        }

        monthly_revenue = self.bookings.filter(
            created_at__date__gte=month_start,
            status__in=['confirmed', 'completed']
        ).aggregate(total=Sum('total_amount'))

        stats['monthly_revenue'] = monthly_revenue['total'] or 0

        return stats
