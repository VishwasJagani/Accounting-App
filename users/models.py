# Django
import os
from django.db import models
from random import randint
from datetime import datetime, timedelta

# Local
from base_files.base_models import BaseModel


class RoleModel(BaseModel):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        db_table = "Roles"

    def __str__(self):
        return self.role_name


class User(BaseModel):
    user_id = models.AutoField(primary_key=True)
    user_role = models.ForeignKey(
        RoleModel, on_delete=models.CASCADE, related_name='user_role', blank=True, null=True)
    fullname = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_image = models.ImageField(
        upload_to="user_profile/", blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    work_address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "Users"

    def __str__(self):
        return self.fullname

    def save(self, *args, **kwargs):
        try:
            if self.pk:
                old_user = User.objects.filter(pk=self.pk).first()
                if old_user and old_user.profile_image and old_user.profile_image != self.profile_image:
                    if os.path.isfile(old_user.profile_image.path):
                        os.remove(old_user.profile_image.path)
        except Exception:
            pass

        super().save(*args, **kwargs)


class Otp(BaseModel):
    otp_id = models.AutoField(primary_key=True)
    user = models.CharField(max_length=50, blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_type = models.CharField(max_length=20, blank=True, null=True)
    expiry_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        db_table = "OTPs"

    def __str__(self):
        return f"{self.user} - {self.otp_type}"

    def save(self, *args, **kwargs):
        try:
            if not self.otp:
                self.otp = str(randint(100000, 999999))
            if not self.expiry_time:
                self.expiry_time = datetime.now() + timedelta(minutes=5)
        except Exception:
            pass
        super().save(*args, **kwargs)


class ClientModel(BaseModel):
    client_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='client_user', blank=True, null=True)
    client_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    tax_number = models.CharField(max_length=20, blank=True, null=True)
    gst_type = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    payment_term = models.CharField(max_length=20, blank=True, null=True)
    credit_limit = models.CharField(max_length=20, blank=True, null=True)
    preferred_payment_method = models.CharField(
        max_length=20, blank=True, null=True)
    bank_details = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        db_table = "Clients"
