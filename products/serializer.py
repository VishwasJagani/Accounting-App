# Rest FrameWork
from rest_framework import serializers

# Django

# Local
from products import models as products_models
from users import models as users_models


class ProductCategorySerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.fullname')

    class Meta:
        model = products_models.ProductCategory
        fields = ['category_id', 'category_name',
                  'user', 'user_name', 'is_active']


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.category_name')

    class Meta:
        model = products_models.Products
        fields = ['product_id', 'name', 'category',
                  'category_name', 'is_active']


class ProductSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.fullname')
    category_name = serializers.ReadOnlyField(source='category.category_name')
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = products_models.Products
        fields = ['product_id', 'user', 'user_name', 'name', 'item_sku', 'description', 'category', 'category_name', 'stock_level',
                  'reorder_point', 'selling_price', 'cost_price', 'tax', 'discount_percentage', 'product_image', 'is_active']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = products_models.PurchaseOrders
        fields = ['order_id', 'user', 'client', 'order_number', 'order_date',
                  'expected_delivery_date', 'subtotal', 'tax', 'total', 'notes', 'order_status']


class OrderItemsSeializer(serializers.ModelSerializer):
    class Meta:
        model = products_models.OrderItems
        fields = ['item_id', 'order', 'product', 'qty', 'price', 'tax']


class ProductDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = products_models.Products
        fields = [
            'product_id', 'name', 'item_sku', 'description', 'category',
            'stock_level', 'reorder_point', 'selling_price', 'cost_price',
            'tax', 'discount_percentage', 'product_image', 'is_active'
        ]


class OrderItemDetailsSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = products_models.OrderItems
        fields = ['item_id', 'product', 'qty', 'price', 'tax']


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = users_models.ClientModel
        # include the fields you need
        fields = ['client_id', 'client_name', 'email', 'phone_number']


class PurchaseOrderDetailsSerializer(serializers.ModelSerializer):
    order_items = OrderItemDetailsSerializer(many=True, read_only=True)
    client = ClientSerializer(read_only=True)

    class Meta:
        model = products_models.PurchaseOrders
        fields = [
            'order_id', 'order_number', 'order_date', 'expected_delivery_date',
            'subtotal', 'tax', 'total', 'notes', 'order_status', 'client', 'order_items'
        ]
