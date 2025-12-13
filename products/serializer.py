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
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = products_models.Products
        fields = ['product_id', 'name', 'category',
                  'category_name', 'item_sku', 'product_image', 'stock_level', 'final_price', 'quantity', 'is_active']

    def get_product_image(self, obj):
        if obj.product_image:
            return obj.product_image.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.fullname')
    category_name = serializers.ReadOnlyField(source='category.category_name')
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = products_models.Products
        fields = ['product_id', 'user', 'user_name', 'name', 'item_sku', 'description', 'category', 'category_name', 'unit_of_measurement', 'stock_level',
                  'reorder_point', 'quantity', 'pcs', 'weight', 'selling_price', 'cost_price', 'profit_margin', 'tax', 'gst_category', 'discount_percentage', 'final_price', 'product_image', 'is_track_inventory', 'is_inter_state_sale', 'is_active']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = products_models.PurchaseOrders
        fields = ['order_id', 'user', 'client', 'order_number', 'order_date',
                  'expected_delivery_date', 'subtotal', 'tax', 'total', 'notes', 'order_status', 'order_type']


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
            'subtotal', 'tax', 'total', 'notes', 'order_status', 'order_type', 'client', 'order_items'
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = products_models.Invoice
        fields = ['invoice_id', 'user', 'client', 'invoice_number', 'issue_date',
                  'payment_due', 'subtotal', 'tax', 'discount', 'total', 'notes', 'payment_method', 'invoice_type']


class InvoiceItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = products_models.InvoiceItems
        fields = ['item_id', 'invoice', 'product', 'qty', 'unit_of_measurement',
                  'price', 'discount_amount', 'tax', 'gst_category', 'is_inter_state_sale', 'weight_based_item']


class InvoiceItemDetailsSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = products_models.InvoiceItems
        fields = ['item_id', 'product', 'qty', 'unit_of_measurement', 'price',
                  'discount_amount', 'tax', 'gst_category', 'is_inter_state_sale', 'weight_based_item']


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = users_models.ClientModel
        # include the fields you need
        fields = ['client_id', 'client_name', 'email', 'phone_number']


class InvoiceDetailsSerializer(serializers.ModelSerializer):
    invoice_items = InvoiceItemDetailsSerializer(many=True, read_only=True)
    client = ClientSerializer(read_only=True)

    class Meta:
        model = products_models.Invoice
        fields = [
            'invoice_id', 'invoice_number', 'issue_date', 'payment_due',
            'subtotal', 'tax', 'discount', 'total', 'notes', 'payment_method', 'client', 'invoice_items', 'invoice_type']


class ActivityLogSerializer(serializers.ModelSerializer):

    user_name = serializers.ReadOnlyField(source='user.fullname')

    class Meta:
        model = products_models.ActivityLog
        fields = ['id', 'user', 'user_name', 'action',
                  'timestamp', 'title', 'description', 'extra_data']
