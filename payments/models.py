from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PlatformAccess(models.Model):
    PAYMENT_STATUS = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="platform_access"
    )
    reference = models.CharField(max_length=200, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.status}"

    class Meta:
        verbose_name_plural = "Platform Access"
