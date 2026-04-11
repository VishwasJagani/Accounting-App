from django.contrib import admin
from admin_panel import models as admin_models


class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ('content', 'is_active')


admin.site.register(admin_models.PrivacyPolicy, PrivacyPolicyAdmin)


class FAQsAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('question', 'answer')
    list_per_page = 10


admin.site.register(admin_models.FAQs, FAQsAdmin)


class TermsAndConditionsAdmin(admin.ModelAdmin):
    list_display = ('content', 'is_active')


admin.site.register(admin_models.TermsAndConditions, TermsAndConditionsAdmin)


class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'country_code',
                    'phone_number', 'is_active')


admin.site.register(admin_models.ContactUs, ContactUsAdmin)


class InquiryAdmin(admin.ModelAdmin):
    list_display = ('topic', 'subject', 'message')
    list_filter = ('topic',)
    search_fields = ('topic', 'subject', 'message')
    list_per_page = 10


admin.site.register(admin_models.Inquiry, InquiryAdmin)


class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('content', 'is_active')


admin.site.register(admin_models.AboutUs, AboutUsAdmin)
