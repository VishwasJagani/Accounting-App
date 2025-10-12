# Django
from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html

# Local
from users import models as users_models


class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name', 'is_active')


admin.site.register(users_models.RoleModel, RoleAdmin)


class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'fullname', 'email',
                    'user_role', 'image_banner')
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ('fullname', 'email')
    list_per_page = 15

    base_url = settings.MEDIA_URL

    def image_banner(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}{}" style="max-width:50px; max-height:50px; border-radius:5px;" />', self.base_url, obj.profile_image)
        else:
            return '-'


admin.site.register(users_models.User, UserAdmin)


class OTPAdmin(admin.ModelAdmin):
    list_display = ('otp_id', 'user', 'otp', 'created_at')
    search_fields = ('user', 'otp')
    list_per_page = 15


admin.site.register(users_models.Otp, OTPAdmin)


class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'client_name', 'email', 'is_active')
    search_fields = ('client_name', 'email')
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 15


admin.site.register(users_models.ClientModel, ClientAdmin)
