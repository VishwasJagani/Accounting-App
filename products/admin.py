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
