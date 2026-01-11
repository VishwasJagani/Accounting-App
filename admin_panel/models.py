# Django
from django.db import models

# Local
from base_files.base_models import BaseModel


class PrivacyPolicy(BaseModel):
    content = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Privacy Policies"
        verbose_name = "Privacy Policy"
        db_table = "privacy_policy"

    def __str__(self):
        return "Privacy Policy"


class FAQs(BaseModel):
    faqs = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "FAQs"
        verbose_name = "FAQ"
        db_table = "faqs"

    def __str__(self):
        return self.faqs[:10] + "..." if len(self.faqs) > 20 else self.faqs
