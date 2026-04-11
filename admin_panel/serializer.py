# Rest FrameWork
from rest_framework import serializers

# Django
from django.template.defaultfilters import timesince

# Local
from admin_panel import models as admin_panel_models
from users import models as users_models


class AdminUserListSerializer(serializers.ModelSerializer):
    last_active = serializers.SerializerMethodField()

    class Meta:
        model = users_models.User
        fields = ['user_id', 'fullname', 'email', 'last_active', 'created_at']

    def get_last_active(self, obj):
        if obj.last_login:
            return timesince(obj.last_login) + " ago"
        return "Never active"


class FAQSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = admin_panel_models.FAQs
        fields = '__all__'


class TermsAndConditionsSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = admin_panel_models.TermsAndConditions
        fields = '__all__'


class ContactUsSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = admin_panel_models.ContactUs
        fields = '__all__'


class InquirySerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = admin_panel_models.Inquiry
        fields = '__all__'


class AboutUsSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = admin_panel_models.AboutUs
        fields = '__all__'
