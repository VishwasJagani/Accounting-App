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
