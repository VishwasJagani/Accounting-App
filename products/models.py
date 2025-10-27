# Django
import os
from django.db import models
from django.utils.timezone import now
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
    unit_of_measurement = models.CharField(
        max_length=100, blank=True, null=True)
    stock_level = models.IntegerField(default=0, blank=True, null=True)
    reorder_point = models.IntegerField(default=0, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    pcs = models.IntegerField(blank=True, null=True)
    weight = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    selling_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    profit_margin = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    tax = models.CharField(max_length=100, blank=True, null=True)
    gst_category = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percentage = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    product_image = models.ImageField(
        upload_to="product_images/", blank=True, null=True)
    final_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    is_track_inventory = models.BooleanField(default=False)
    is_inter_state_sale = models.BooleanField(default=False)
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


class PurchaseOrders(BaseModel):
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        users_models.User, on_delete=models.CASCADE, blank=True, null=True, related_name="user_purchase_order")
    client = models.ForeignKey(
        users_models.ClientModel, on_delete=models.CASCADE, blank=True, null=True, related_name="client_purchase_order")
    order_number = models.CharField(
        max_length=255, blank=True, null=True, unique=True)
    order_date = models.DateField(blank=True, null=True)
    expected_delivery_date = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(
        blank=True, null=True, max_digits=10, decimal_places=2)
    tax = models.DecimalField(blank=True, null=True,
                              max_digits=10, decimal_places=2)
    total = models.DecimalField(
        blank=True, null=True, max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    order_status = models.CharField(
        max_length=100, blank=True, null=True, default="Pending")

    class Meta:
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
        db_table = "PurchaseOrders"

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number and self.user:
            prefix = ''.join([c for c in self.user.fullname if c.isalpha()])[
                :2].upper()
            year = now().year
            base_prefix = f"{prefix}-{year}"

            # Get latest order for this user in current year
            latest_order = PurchaseOrders.objects.filter(
                user=self.user,
                order_number__startswith=base_prefix
            ).order_by('-order_number').first()

            if latest_order and latest_order.order_number:
                try:
                    # Extract the sequence number and increment it
                    last_seq = int(latest_order.order_number.split('-')[-1])
                    next_seq = f"{last_seq + 1:02d}"
                except:
                    next_seq = "01"
            else:
                next_seq = "01"

            self.order_number = f"{base_prefix}-{next_seq}"

        super().save(*args, **kwargs)


class OrderItems(BaseModel):
    item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        PurchaseOrders, on_delete=models.CASCADE, blank=True, null=True, related_name="order_items")
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, blank=True, null=True, related_name="order_product")
    qty = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(
        blank=True, null=True, max_digits=10, decimal_places=2)
    tax = models.DecimalField(
        blank=True, null=True, max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        db_table = "orderitems"

    def __str__(self):
        return f"{self.product.name} - {self.qty} items"
