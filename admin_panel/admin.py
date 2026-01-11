from django.contrib import admin
from admin_panel import models as admin_models


class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ('content', 'is_active')


admin.site.register(admin_models.PrivacyPolicy, PrivacyPolicyAdmin)


class FAQsAdmin(admin.ModelAdmin):
    list_display = ('faqs', 'is_active')


admin.site.register(admin_models.FAQs, FAQsAdmin)
