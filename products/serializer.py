# Rest FrameWork
from rest_framework import serializers

# Django

# Local
from products import models as products_models


class ProductCategorySerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.fullname')

    class Meta:
        model = products_models.ProductCategory
        fields = ['category_id', 'category_name', 'user', 'user_name', 'is_active']


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.category_name')

    class Meta:
        model = products_models.Products
        fields = ['product_id', 'name', 'category', 'category_name', 'is_active']


class ProductSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.fullname')
    category_name = serializers.ReadOnlyField(source='category.category_name')
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = products_models.Products
        fields = ['product_id', 'user', 'user_name', 'name', 'item_sku', 'description', 'category', 'category_name', 'stock_level',
                  'reorder_point', 'selling_price', 'cost_price', 'tax', 'discount_percentage', 'product_image', 'is_active']
