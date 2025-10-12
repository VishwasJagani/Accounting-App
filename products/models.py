# Django
import os
from django.db import models
from random import randint
from datetime import datetime, timedelta

# Local
from base_files.base_models import BaseModel
from users import models as users_models


class ProductCategory(BaseModel):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(users_models.User, on_delete=models.CASCADE,
                             blank=True, null=True, related_name="category_products")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"
        db_table = "ProductCategories"

    def __str__(self):
        return self.category_name


class Products(BaseModel):
    product_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        users_models.User, on_delete=models.CASCADE, blank=True, null=True, related_name="user_products")
    name = models.CharField(max_length=255, blank=True, null=True)
    item_sku = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        ProductCategory, on_delete=models.CASCADE, blank=True, null=True, related_name="category_products")
    stock_level = models.IntegerField(default=0, blank=True, null=True)
    reorder_point = models.IntegerField(default=0, blank=True, null=True)
    selling_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    tax = models.CharField(max_length=100, blank=True, null=True)
    discount_percentage = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    product_image = models.ImageField(
        upload_to="product_images/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        db_table = "Products"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        try:
            if self.pk:
                old_product = Products.objects.filter(pk=self.pk).first()
                if old_product and old_product.product_image and old_product.product_image != self.product_image:
                    if os.path.isfile(old_product.product_image.path):
                        os.remove(old_product.product_image.path)
        except Exception:
            pass

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            if self.product_image and os.path.isfile(self.product_image.path):
                os.remove(self.product_image.path)
        except Exception:
            pass

        super().delete(*args, **kwargs)
