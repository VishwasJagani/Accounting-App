# Django
from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html

# Local
from products import models as products_models


class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_id', 'category_name', 'user', 'is_active')
    search_fields = ['category_name']
    list_per_page = 15


admin.site.register(products_models.ProductCategory, ProductCategoryAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'name', 'category',
                    'is_active', 'image_banner')
    search_fields = ['name']
    list_filter = ('category', 'is_active')
    list_per_page = 15

    base_url = settings.MEDIA_URL

    def image_banner(self, obj):
        if obj.product_image:
            return format_html('<img src="{}{}" style="max-width:50px; max-height:50px; border-radius:5px;" />', self.base_url, obj.product_image)
        else:
            return '-'


admin.site.register(products_models.Products, ProductAdmin)


class PurchaseOrdersAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'client', 'order_number',
                    'order_date', 'expected_delivery_date', 'order_type')
    search_fields = ['order_number', 'user__fullname',
                     'user__email', 'client__client_name', 'client__email']
    list_per_page = 15
    list_filter = ('user', 'client', 'order_date', 'expected_delivery_date')


admin.site.register(products_models.PurchaseOrders, PurchaseOrdersAdmin)


class PurchaseOrderItemsAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'order', 'product', 'qty', 'price', 'tax')
    search_fields = ['product__name']
    list_per_page = 15
    list_filter = ('product',)


admin.site.register(products_models.OrderItems,
                    PurchaseOrderItemsAdmin)


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'user', 'client',
                    'invoice_number', 'payment_due', 'total')
    search_fields = ['invoice_number', 'user__fullname',
                     'user__email', 'client__client_name', 'client__email']
    list_per_page = 15
    list_filter = ('user', 'client', 'issue_date', 'payment_due')


admin.site.register(products_models.Invoice, InvoiceAdmin)


class InvoiceItemsAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'invoice', 'product', 'qty', 'price', 'tax')
    search_fields = ['product__name']
    list_per_page = 15
    list_filter = ('product',)


admin.site.register(products_models.InvoiceItems, InvoiceItemsAdmin)


class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'title')
    search_fields = ['user__fullname', 'user__email', 'action', 'title']
    list_per_page = 20
    list_filter = ('action',)


admin.site.register(products_models.ActivityLog, ActivityLogAdmin)
