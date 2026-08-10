"""
Product and Package models for Event Planner project.
"""

from django.db import models

from apps.common.models import BusinessScopedModel


class Product(BusinessScopedModel):
    """
    Product model representing individual items or services.
    """

    CATEGORY_CHOICES = [
        ('service', 'Service'),
        ('rental', 'Rental'),
        ('consumable', 'Consumable'),
        ('decoration', 'Decoration'),
        ('food', 'Food & Beverage'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=50, blank=True, help_text="e.g., per piece, per hour, per pax")
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.business.name})"


class Package(BusinessScopedModel):
    """
    Package model representing bundled products/services.
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    products = models.ManyToManyField(
        Product,
        related_name='packages',
        through='PackageItem'
    )
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    min_pax = models.PositiveIntegerField(default=1)
    max_pax = models.PositiveIntegerField(null=True, blank=True)
    price_per_additional_pax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Additional price per person above min_pax"
    )
    inclusions = models.JSONField(default=list, blank=True, help_text="List of included items/features")
    image = models.ImageField(upload_to='package_images/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    def calculate_price(self, pax_count):
        """
        Calculate total price based on pax count.
        """
        if pax_count <= self.min_pax:
            return self.base_price

        additional_pax = pax_count - self.min_pax
        return self.base_price + (additional_pax * self.price_per_additional_pax)


class PackageItem(models.Model):
    """
    Through model for Package-Product relationship.
    """

    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['package', 'product']

    def __str__(self):
        return f"{self.product.name} x{self.quantity} in {self.package.name}"
