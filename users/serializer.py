# Rest FrameWork
from rest_framework import serializers

# Django
from django.contrib.auth.hashers import make_password

# Local
from users import models as users_models


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = users_models.RoleModel
        fields = ['role_id', 'role_name', 'is_active']


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(
        source='user_role.role_name', read_only=True)

    class Meta:
        model = users_models.User
        fields = ['user_id', 'fullname', 'email', 'password', 'user_role', 'role_name', 'country_code', 'phone_number', 'date_of_birth',
                  'profile_image', 'address', 'work_address', 'is_active', 'is_email_verified', 'is_phone_verified', 'is_admin']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.get('password')
        if password:
            validated_data['password'] = make_password(
                password)  # hash password
        return users_models.User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.get('password')
        if password:
            validated_data['password'] = make_password(password)
        return super().update(instance, validated_data)


class ClientListSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    # user_fullname = serializers.ReadOnlyField(source='user.fullname')

    class Meta:
        model = users_models.ClientModel
        fields = ['client_id', 'user', 'client_name',
                  'email', 'phone_number', 'user_type', 'is_favorite', 'created_at', 'updated_at']

    def get_created_at(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_updated_at(self, obj):
        if obj.updated_at:
            return obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        return None


class ClientSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    user_fullname = serializers.ReadOnlyField(source='user.fullname')

    class Meta:
        model = users_models.ClientModel
        fields = ['client_id', 'user', 'user_fullname', 'client_name', 'email', 'phone_number', 'contact_person', 'shipping_address',
                  'billing_address', 'city', 'state', 'country', 'zip_code', 'tax_number', 'gst_type', 'pan_number', 'payment_term', 'credit_limit', 'preferred_payment_method', 'bank_details', 'notes', 'category', 'user_type', 'created_at', 'updated_at']

    def get_created_at(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_updated_at(self, obj):
        if obj.updated_at:
            return obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        return None
