"""
Base models for Event Planner project.
"""

from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with common timestamp fields.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BusinessScopedModel(BaseModel):
    """
    Abstract model for business-scoped entities.
    """

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )

    class Meta:
        abstract = True
