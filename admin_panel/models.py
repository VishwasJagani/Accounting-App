# Django
from django.db import models

# Local
from base_files.base_models import BaseModel


class PrivacyPolicy(BaseModel):
    content = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Privacy Policies"
        verbose_name = "Privacy Policy"
        db_table = "privacy_policy"

    def __str__(self):
        return "Privacy Policy"


class FAQs(BaseModel):
    question = models.TextField(blank=True, null=True)
    answer = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "FAQs"
        verbose_name = "FAQ"
        db_table = "faqs"

    def __str__(self):
        return self.faqs[:10] + "..." if len(self.faqs) > 20 else self.faqs


class TermsAndConditions(BaseModel):
    content = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Terms and Conditions"
        verbose_name = "Terms and Condition"
        db_table = "terms_and_conditions"

    def __str__(self):
        return "Terms and Conditions"


class ContactUs(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Contact Us"
        verbose_name = "Contact Us"
        db_table = "contact_us"

    def __str__(self):
        return self.name


class Inquiry(BaseModel):
    topic = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Inquiries"
        verbose_name = "Inquiry"
        db_table = "inquiry"

    def __str__(self):
        return self.name


class AboutUs(BaseModel):
    content = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "About Us"
        verbose_name = "About Us"
        db_table = "about_us"

    def __str__(self):
        return "About Us"
