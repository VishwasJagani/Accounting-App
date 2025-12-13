# Django
import os
from drf_yasg import openapi
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema

# Rest FrameWork
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response

# Local
from base_files.base_permission import IsAuthenticated
from base_files.base_pagination import CustomPagination
from users import utils as users_utils
from products import serializer as products_serializer
from products import models as products_models
from decimal import Decimal


class ProductCategoryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = products_serializer.ProductCategorySerializer

    def get_queryset(self, user):
        return products_models.ProductCategory.objects.filter(
            user=user,
            is_deleted=False,
            is_active=True
        ).order_by('-created_at')

    @swagger_auto_schema(
        operation_summary="List Product Categories",
        operation_description="Retrieve a list of all active (non-deleted) product categories ordered by creation date.",
        tags=['Products Category'],
        responses={
            200: openapi.Response(
                description="List of product categories",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Product Category Fetched"),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            # Will override below with actual serializer
                            items=openapi.Items(type=openapi.TYPE_OBJECT)
                        ),
                    }
                ),
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Product Category Fetched",
                        "data": [
                            {
                                "category_id": 1,
                                "category_name": "Electronics",
                                "is_active": "2023-01-01T00:00:00Z"
                            }
                        ]
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Error message"),
                    }
                )
            ),
        }
    )
    def get(self, request):
        try:
            user = request.user
            queryset = self.get_queryset(user)
            serializer = self.serializer_class(queryset, many=True)
            return Response({"success": True, "message": "Product Category Fetched", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AddProductCategory(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = products_serializer.ProductCategorySerializer

    @swagger_auto_schema(
        operation_summary="Add Product Category",
        operation_description="Create a new product category. The name must be unique and not previously deleted.",
        tags=['Products Category'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['category_name'],
            properties={
                'category_name': openapi.Schema(type=openapi.TYPE_STRING, example='Electronics'),
            },
        ),
        responses={
            201: openapi.Response(
                description="Product category successfully created",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Product Category Added'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'category_name': openapi.Schema(type=openapi.TYPE_STRING, example='electronics'),
                                'created_at': openapi.Schema(type=openapi.FORMAT_DATETIME, example='2025-10-07T14:00:00Z'),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request (validation failed or duplicate name)",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Product Category Name already exists"
                        ),
                    }
                )
            ),
        }
    )
    def post(self, request):
        try:
            user = request.user
            data = request.data
            category_name = data.get('category_name')

            if users_utils.is_required(category_name):
                return Response({"success": False, "message": "Product Category Name Is required"}, status=status.HTTP_400_BAD_REQUEST)

            category_name = category_name.lower()

            if products_models.ProductCategory.objects.filter(category_name=category_name, is_deleted=False).exists():
                return Response({"success": False, "message": "Product Category Name already exists"}, status=status.HTTP_400_BAD_REQUEST)

            data['user'] = user.user_id
            data['category_name'] = category_name
            serializer = self.serializer_class(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "Product Category Added", "data": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProductCategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = products_serializer.ProductCategorySerializer

    @swagger_auto_schema(
        operation_summary="Get Product Category Details",
        operation_description="Retrieve a product category by its ID if it exists and is not deleted.",
        tags=["Products Category"],
        manual_parameters=[
            openapi.Parameter(
                name='category_id',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                required=True,
                description='ID of the product category to retrieve'
            )
        ],
        responses={
            200: openapi.Response(
                description="Product category retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Product Category Data Fetched"),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "category_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                "category_name": openapi.Schema(type=openapi.TYPE_STRING, example="electronics"),
                                "created_at": openapi.Schema(type=openapi.FORMAT_DATETIME, example="2025-10-07T14:00:00Z"),
                                # Add more fields from your serializer if applicable
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request (e.g. missing category ID)",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Category ID is required"),
                    }
                )
            ),
            404: openapi.Response(
                description="Category not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Product Category Not Found"),
                    }
                )
            )
        }
    )
    def get(self, request, category_id):
        try:
            user = request.user

            if users_utils.is_required(category_id):
                return Response({"success": False, "message": "Category ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                category = products_models.ProductCategory.objects.get(
                    category_id=category_id, user=user, is_deleted=False)

                serializer = self.serializer_class(category)

                return Response({"success": True, "message": "Product Category Data Fetched", "data": serializer.data}, status=status.HTTP_200_OK)

            except products_models.ProductCategory.DoesNotExist:
                return Response({"success": False, "message": "Product Category Not Found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update Product Category",
        operation_description="Update the name of an existing product category. The new name must be unique.",
        tags=["Products Category"],
        manual_parameters=[
            openapi.Parameter(
                name='category_id',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                required=True,
                description='ID of the product category to update'
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[],
            properties={
                'category_name': openapi.Schema(type=openapi.TYPE_STRING, example="home appliances")
            }
        ),
        responses={
            200: openapi.Response(
                description="Category updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Product Category Updated"),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'category_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'category_name': openapi.Schema(type=openapi.TYPE_STRING, example="home appliances"),
                                'created_at': openapi.Schema(type=openapi.FORMAT_DATETIME, example="2025-10-07T14:00:00Z"),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Validation error or bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Product Category Name already exists")
                    }
                )
            ),
            404: openapi.Response(
                description="Category not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Product Category Not Found")
                    }
                )
            ),
        }
    )
    def put(self, request, category_id):
        try:
            user = request.user
            data = request.data
            category_name = data.get('category_name')

            if category_name:
                if products_models.ProductCategory.objects.filter(category_name=category_name.lower(), user=user, is_deleted=False).exclude(category_id=category_id).exists():
                    return Response({"success": False, "message": "Product Category Name already exists"}, status=status.HTTP_400_BAD_REQUEST)

                data['category_name'] = category_name.lower()

            try:
                category_obj = products_models.ProductCategory.objects.get(
                    category_id=category_id, is_deleted=False)
            except products_models.ProductCategory.DoesNotExist:
                return Response({"success": False, "message": "Product Category Not Found"}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.serializer_class(
                category_obj, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "Product Category Updated", "data": serializer.data}, status=status.HTTP_200_OK)

            return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete a Product Category",
        operation_description="Deletes a product category by its ID if it exists and is not deleted.",
        tags=["Products Category"],
        manual_parameters=[
            openapi.Parameter(
                name='category_id',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                required=True,
                description='ID of the product category to delete'
            )
        ],
        responses={
            200: openapi.Response(
                description="Product category deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Product Category Deleted"),
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request (e.g. missing category ID or invalid request)",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Category ID is required"),
                    }
                )
            ),
            404: openapi.Response(
                description="Category not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Category Not Found"),
                    }
                )
            ),
        }
    )
    def delete(self, request, category_id):
        try:
            user = request.user
            if users_utils.is_required(category_id):
                return Response({"success": False, "message": "Category ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                category = products_models.ProductCategory.objects.get(
                    category_id=category_id, user=user, is_deleted=False)

                category.delete()

                return Response({"success": True, "message": "Product Category Deleted"}, status=status.HTTP_200_OK)

            except products_models.ProductCategory.DoesNotExist:
                return Response({"success": False, "message": "Category Not Found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"success": False, "message": e}, status=status.HTTP_400_BAD_REQUEST)


class ProductListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = products_serializer.ProductListSerializer

    def get_queryset(self, request):
        user = request.user
        product_obj = products_models.Products.objects.filter(
            user=user, is_deleted=False).order_by('-created_at')

        return product_obj

    @swagger_auto_schema(
        operation_summary="Get Product List",
        operation_description="Retrieve a list of products for the authenticated user that are not deleted.",
        tags=["Products"],
        responses={
            200: openapi.Response(
                description="Successfully retrieved the list of products",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Product Data Fetched"),
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                    "name": openapi.Schema(type=openapi.TYPE_STRING, example="Product A"),
                                    "price": openapi.Schema(type=openapi.TYPE_STRING, example="100.00"),
                                    "created_at": openapi.Schema(type=openapi.FORMAT_DATETIME, example="2025-10-01T12:00:00Z"),
                                    "updated_at": openapi.Schema(type=openapi.FORMAT_DATETIME, example="2025-10-01T12:00:00Z"),
                                    # Add any other fields from your product serializer here
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request (e.g., incorrect input or internal error)",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Error message"),
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            category = request.query_params.get('category', None)
            queryset = self.get_queryset(request)
            if category:
                queryset = queryset.filter(category=category)
            serializer = self.serializer_class(queryset, many=True)

            total_value = 0

            for data in serializer.data:
                if data['final_price'] is not None and data['quantity'] is not None:
                    total_value += float(data['final_price']) * \
                        int(data['quantity'])

            return Response({"success": True, "message": "Product Data Fetched", "data": serializer.data, "total_value": total_value}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AddProductView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = products_serializer.ProductSerializer

    @swagger_auto_schema(
        operation_summary="Add a new product",
        operation_description="Adds a new product for the authenticated user after validating required fields.",
        tags=["Products"],
        request_body=products_serializer.ProductSerializer,
        responses={
            201: openapi.Response(
                description="Product added successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Product added successfully."),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                "name": openapi.Schema(type=openapi.TYPE_STRING, example="Product A"),
                                "item_sku": openapi.Schema(type=openapi.TYPE_STRING, example="SKU12345"),
                                "category": openapi.Schema(type=openapi.TYPE_STRING, example="electronics"),
                                "product_image": openapi.Schema(type=openapi.TYPE_STRING, example="https://example.com/product_image.jpg"),
                                "user": openapi.Schema(type=openapi.TYPE_INTEGER, example=123),
                                "created_at": openapi.Schema(type=openapi.FORMAT_DATETIME, example="2025-10-07T14:00:00Z"),
                                "updated_at": openapi.Schema(type=openapi.FORMAT_DATETIME, example="2025-10-07T14:00:00Z"),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request (e.g., missing required fields or invalid data)",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Product Name is required."),
                    }
                )
            )
        },
    )
    def post(self, request):
        try:
            data = request.data
            user = request.user
            name = data.get('name')
            item_sku = data.get('item_sku')
            category = data.get('category')
            product_image = data.get('product_image')

            if users_utils.is_required(name):
                return Response({"success": False, "message": "Product Name is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(item_sku):
                return Response({"success": False, "message": "Item SKU is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(category):
                return Response({"success": False, "message": "Product Category is required."}, status=status.HTTP_400_BAD_REQUEST)

            # if products_models.Products.objects.filter(name=name.lower(), user=user, is_deleted=False).exists():
            #     return Response({"success": False, "message": "Product Name already exists."}, status=status.HTTP_400_BAD_REQUEST)

            # if products_models.Products.objects.filter(item_sku=item_sku.lower(), user=user, is_deleted=False).exists():
            #     return Response({"success": False, "message": "Item SKU already exists."}, status=status.HTTP_400_BAD_REQUEST)

            if not products_models.ProductCategory.objects.filter(category_id=category, is_active=True, is_deleted=False).exists():
                return Response({"success": False, "message": "Invalid Product Category."}, status=status.HTTP_400_BAD_REQUEST)

            if product_image:
                if not users_utils.is_valid_image(product_image):
                    return Response({"success": False, "message": "Invalid Image Format."}, status=status.HTTP_400_BAD_REQUEST)

            data['user'] = user.user_id
            serializer = self.serializer_class(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "Product added successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer = products_serializer.ProductSerializer

    @swagger_auto_schema(
        operation_description="Fetch details of a product for a specific user",
        operation_id="get_product_details",
        tags=["Products"],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Product data fetched successfully",
                schema=products_serializer.ProductSerializer,
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad request or Product not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
        },
        parameters=[
            openapi.Parameter(
                'product_id', openapi.IN_PATH, description="ID of the product to fetch",
                type=openapi.TYPE_INTEGER, required=True
            ),
        ]
    )
    def get(self, request, product_id):
        try:
            user = request.user

            if users_utils.is_required(product_id):
                return Response({"success": False, "message": "Product Id "}, status=status.HTTP_400_BAD_REQUEST)

            product = products_models.Products.objects.filter(
                product_id=product_id, user=user, is_deleted=False).first()

            if not product:
                return Response({"success": False, "message": "Product Not Found."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.serializer(product)
            return Response({"success": True, "message": "Product Data Fetched", "data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Update a product's details for a specific user",
        operation_id="update_product_details",
        tags=["Products"],
        request_body=products_serializer.ProductSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Product updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'item_sku': openapi.Schema(type=openapi.TYPE_STRING),
                                'description': openapi.Schema(type=openapi.TYPE_STRING),
                                'category': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'category_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'unit_of_measurement': openapi.Schema(type=openapi.TYPE_STRING),
                                'stock_level': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'reorder_point': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'pcs': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'weight': openapi.Schema(type=openapi.TYPE_STRING),
                                'selling_price': openapi.Schema(type=openapi.TYPE_STRING),
                                'cost_price': openapi.Schema(type=openapi.TYPE_STRING),
                                'profit_margin': openapi.Schema(type=openapi.TYPE_STRING),
                                'tax': openapi.Schema(type=openapi.TYPE_STRING),
                                'gst_category': openapi.Schema(type=openapi.TYPE_STRING),
                                'final_price': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_track_inventory': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'is_inter_state_sale': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'discount_percentage': openapi.Schema(type=openapi.TYPE_STRING),
                                'product_image': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        ),
                    }
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad request or invalid data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
        },
        parameters=[
            openapi.Parameter(
                'product_id', openapi.IN_PATH, description="ID of the product to update",
                type=openapi.TYPE_INTEGER, required=True
            ),
        ]
    )
    def put(self, request, product_id):
        try:
            user = request.user
            data = request.data
            category = data.get('category')
            product_image = data.get('product_image')

            if users_utils.is_required(product_id):
                return Response({"success": False, "message": "Product Id "}, status=status.HTTP_400_BAD_REQUEST)

            if category:
                if not products_models.ProductCategory.objects.filter(category_id=category, is_active=True, is_deleted=False).exists():
                    return Response({"success": False, "message": "Invalid Product Category."}, status=status.HTTP_400_BAD_REQUEST)

            if product_image:
                if not users_utils.is_valid_image(product_image):
                    return Response({"success": False, "message": "Invalid Image Format."}, status=status.HTTP_400_BAD_REQUEST)

            product = products_models.Products.objects.filter(
                product_id=product_id, user=user, is_deleted=False).first()

            if not product:
                return Response({"success": False, "message": "Product Not Found."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.serializer(product, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "Product Updated Successfully", "data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a product by its ID for a specific user",
        operation_id="delete_product",
        tags=["Products"],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Product deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad request or product not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
        },
        parameters=[
            openapi.Parameter(
                'product_id', openapi.IN_PATH, description="ID of the product to delete",
                type=openapi.TYPE_INTEGER, required=True
            ),
        ]
    )
    def delete(self, request, product_id):
        try:
            user = request.user

            if users_utils.is_required(product_id):
                return Response({"success": False, "message": "Product Id "}, status=status.HTTP_400_BAD_REQUEST)

            product = products_models.Products.objects.filter(
                product_id=product_id, user=user, is_deleted=False).first()

            if not product:
                return Response({"success": False, "message": "Product Not Found."}, status=status.HTTP_400_BAD_REQUEST)

            if product.product_image:
                os.remove(product.product_image.path)

            product.delete()

            return Response({"success": True, "message": "Product Deleted Successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = products_serializer.PurchaseOrderSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        order_type = self.request.query_params.get('order_type', None)

        order_data = products_models.PurchaseOrders.objects.filter(
            user=user, is_deleted=False).order_by('-created_at')

        if order_type:
            order_data = order_data.filter(order_type=order_type)

        response_data = []

        for order in order_data:
            items = products_models.OrderItems.objects.filter(
                order=order)

            total_items = items.count()

            response_data.append({
                'order_id': order.order_id,
                'client': order.client.client_name,
                'order_number': order.order_number,
                'total_items': total_items,
                'total_price': order.total,
                'order_status': order.order_status
            })

        return response_data

    @swagger_auto_schema(
        operation_summary="Get Purchase Order List",
        operation_description="Retrieve a list of purchase orders for the authenticated user that are not deleted.",
        tags=["Purchase Orders"],
        responses={
            200: openapi.Response(
                description="Successfully retrieved the list of purchase orders",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Purchase orders fetched successfully"),
                        "count": openapi.Schema(type=openapi.TYPE_INTEGER, example=25),
                        "next": openapi.Schema(type=openapi.FORMAT_URI, example="http://api.example.com/orders?page=2"),
                        "previous": openapi.Schema(type=openapi.FORMAT_URI, example=None),
                        "results": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "order_id": openapi.Schema(type=openapi.TYPE_STRING, example="PO-123456"),
                                    "client": openapi.Schema(type=openapi.TYPE_STRING, example="Acme Corp"),
                                    "order_number": openapi.Schema(type=openapi.TYPE_STRING, example="ORD-78910"),
                                    "total_items": openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                                    "total_price": openapi.Schema(type=openapi.TYPE_STRING, example="499.99"),
                                    "order_status": openapi.Schema(type=openapi.TYPE_STRING, example="Completed"),
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="An error occurred"),
                    }
                )
            )
        }
    )
    def get(self, request):
        try:
            response_data = self.get_queryset()
            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(
                response_data, request)

            return paginator.get_paginated_response(result_page)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreatePurchaseOrderView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = products_serializer.PurchaseOrderSerializer

    @swagger_auto_schema(
        operation_summary="Create Purchase Order",
        operation_description="Creates a new purchase order along with its items.",
        tags=["Purchase Orders"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["client", "order_date", "expected_delivery_date",
                      "subtotal", "tax", "total", "items"],
            properties={
                "client": openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                "order_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-10-15"),
                "expected_delivery_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-10-20"),
                "subtotal": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=1000.0),
                "tax": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=10.0),
                "total": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=1200.0),
                "items": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=["product_id", "qty", "tax"],
                        properties={
                            "product_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=4),
                            "qty": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                            "tax": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=10.0)
                        }
                    )
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Purchase Order Created Successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Purchase Order Created Successfully"),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "order_id": openapi.Schema(type=openapi.TYPE_STRING, example="PO-1001"),
                                "client": openapi.Schema(type=openapi.TYPE_STRING, example="Acme Corp"),
                                "order_number": openapi.Schema(type=openapi.TYPE_STRING, example="ORD-20251015"),
                                "order_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-10-15"),
                                "expected_delivery_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-10-20"),
                                "subtotal": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=1000.0),
                                "tax": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=10.0),
                                "total": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=1200.0),
                                "order_status": openapi.Schema(type=openapi.TYPE_STRING, example="Pending"),
                                "order_items": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "order": openapi.Schema(type=openapi.TYPE_STRING, example="PO-1001"),
                                            "product": openapi.Schema(type=openapi.TYPE_INTEGER, example=4),
                                            "qty": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                            "price": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=1000.0),
                                            "tax": openapi.Schema(type=openapi.TYPE_NUMBER, format="float", example=10.0)
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request - Validation or internal error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Client ID is required")
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            user = request.user
            data = request.data
            client = data.get('client')
            items = data.get('items')
            order_type = data.get('order_type')

            if users_utils.is_required(client):
                return Response({"success": False, "message": "Client ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(order_type):
                return Response({"success": False, "message": "Order type is required"}, status=status.HTTP_400_BAD_REQUEST)

            if order_type and order_type not in ["purchase", "sales"]:
                return Response({"success": False, "message": "Invalid order type"}, status=status.HTTP_400_BAD_REQUEST)

            if items:
                for item in items:
                    if users_utils.is_required(item.get('qty')):
                        return Response({"success": False, "message": "Quantity is required."}, status=status.HTTP_400_BAD_REQUEST)

                    if not products_models.Products.objects.filter(product_id=item.get('product_id'), user=user, is_deleted=False).exists():
                        return Response({"success": False, "message": "Invalid Product ID."}, status=status.HTTP_400_BAD_REQUEST)

            data['user'] = user.user_id
            serializer = self.serializer_class(data=data)

            if serializer.is_valid():
                order_instance = serializer.save()

                if items:
                    item_list = []
                    for item in items:
                        product = products_models.Products.objects.get(
                            product_id=item.get('product_id'), user=user, is_deleted=False)

                        item_data = {
                            'order': order_instance.order_id,
                            'product': product.product_id,
                            'qty': item.get('qty'),
                            'price': product.selling_price,
                            'tax': item.get('tax')
                        }

                        items_serializer = products_serializer.OrderItemsSeializer(
                            data=item_data)
                        if items_serializer.is_valid():
                            items_serializer.save()
                            item_list.append(items_serializer.data)

                        else:
                            return Response({"success": False, "error": items_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                products_models.ActivityLog.objects.create(
                    user=user,
                    action="purchase_order" if order_type == "purchase" else "sales_order",
                    title=f"{'Purchase' if order_type == 'purchase' else 'Sales'} Order Created - {order_instance.order_number}",
                    description=f"New {'Purchase' if order_type == 'purchase' else 'Sales'} Order Created - {order_instance.order_number} from {order_instance.client.client_name}",
                    extra_data={
                        "order_id": order_instance.order_id,
                        "amount": float(order_instance.total),
                    },
                )

                response_data = self.serializer_class(order_instance).data
                response_data['order_items'] = item_list

                return Response({"success": True, "message": "Purchase Order Created Successfully", "data": response_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Purchase Order Detail",
        operation_description="Retrieve the details of a specific purchase order by ID for the authenticated user.",
        tags=["Purchase Orders"],
        responses={
            200: openapi.Response(
                description="Successfully retrieved the purchase order details",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Purchase Order Details Fetched"),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "order_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=11),
                                "order_number": openapi.Schema(type=openapi.TYPE_STRING, example="AB-2025-01"),
                                "order_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-10-15"),
                                "expected_delivery_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-10-20"),
                                "subtotal": openapi.Schema(type=openapi.TYPE_STRING, example="10000.00"),
                                "tax": openapi.Schema(type=openapi.TYPE_STRING, example="100.00"),
                                "total": openapi.Schema(type=openapi.TYPE_STRING, example="12000.00"),
                                "notes": openapi.Schema(type=openapi.TYPE_STRING, example=""),
                                "order_status": openapi.Schema(type=openapi.TYPE_STRING, example="Pending"),
                                "client": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "client_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                                        "client_name": openapi.Schema(type=openapi.TYPE_STRING, example="Demo"),
                                        "email": openapi.Schema(type=openapi.TYPE_STRING, example="demo@gmail.com"),
                                        "phone_number": openapi.Schema(type=openapi.TYPE_STRING, example="12345678"),
                                    }
                                ),
                                "order_items": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "item_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=6),
                                            "product": openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                properties={
                                                    "product_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=4),
                                                    "user": openapi.Schema(type=openapi.TYPE_INTEGER, example=6),
                                                    "user_name": openapi.Schema(type=openapi.TYPE_STRING, example="ABC Patel"),
                                                    "name": openapi.Schema(type=openapi.TYPE_STRING, example="Switch"),
                                                    "item_sku": openapi.Schema(type=openapi.TYPE_STRING, example="sw-100q1"),
                                                    "description": openapi.Schema(type=openapi.TYPE_STRING, example="affsdfcd"),
                                                    "category": openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                                                    "category_name": openapi.Schema(type=openapi.TYPE_STRING, example="electronics"),
                                                    "stock_level": openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                                                    "reorder_point": openapi.Schema(type=openapi.TYPE_INTEGER, example=20),
                                                    "selling_price": openapi.Schema(type=openapi.TYPE_STRING, example="100.00"),
                                                    "cost_price": openapi.Schema(type=openapi.TYPE_STRING, example="50.00"),
                                                    "tax": openapi.Schema(type=openapi.TYPE_STRING, example="GST"),
                                                    "discount_percentage": openapi.Schema(type=openapi.TYPE_STRING, example="5.00"),
                                                    "product_image": openapi.Schema(type=openapi.TYPE_STRING, example="/media/product_images/photo2.jpg"),
                                                    "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                                                }
                                            ),
                                            "qty": openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                                            "price": openapi.Schema(type=openapi.TYPE_STRING, example="100.00"),
                                            "tax": openapi.Schema(type=openapi.TYPE_STRING, example="100.00"),
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Order ID is required or other error"),
                    }
                )
            ),
            404: openapi.Response(
                description="Purchase order not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="No purchase order found for the given ID"),
                    }
                )
            )
        }
    )
    def get(self, request, order_id):
        try:
            user = request.user

            if users_utils.is_required(order_id):
                return Response({
                    "success": False,
                    "message": "Order ID is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            purchase_order = products_models.PurchaseOrders.objects.prefetch_related(
                'order_items'
            ).filter(order_id=order_id, user=user, is_deleted=False).first()

            if not purchase_order:
                return Response({
                    "success": False,
                    "message": "No purchase order found for the given ID"
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = products_serializer.PurchaseOrderDetailsSerializer(
                purchase_order)
            return Response({
                "success": True,
                "message": "Purchase Order Details Fetched",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update Purchase Order",
        operation_description="Update an existing purchase order and its order items for the authenticated user.",
        tags=["Purchase Orders"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["order_date", "expected_delivery_date",
                      "subtotal", "tax", "total", "items"],
            properties={
                "order_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-10-15"),
                "expected_delivery_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-10-20"),
                "subtotal": openapi.Schema(type=openapi.TYPE_NUMBER, example=10000),
                "tax": openapi.Schema(type=openapi.TYPE_NUMBER, example=100),
                "total": openapi.Schema(type=openapi.TYPE_NUMBER, example=12000),
                "items": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=["product_id", "qty"],
                        properties={
                            "product_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=4),
                            "qty": openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                            "tax": openapi.Schema(type=openapi.TYPE_NUMBER, example=100),
                        }
                    )
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Purchase Order updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Purchase Order updated successfully"),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "order_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=11),
                                "order_number": openapi.Schema(type=openapi.TYPE_STRING, example="PO-2025-001"),
                                "order_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-10-15"),
                                "expected_delivery_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-10-20"),
                                "subtotal": openapi.Schema(type=openapi.TYPE_NUMBER, example=10000),
                                "tax": openapi.Schema(type=openapi.TYPE_NUMBER, example=100),
                                "total": openapi.Schema(type=openapi.TYPE_NUMBER, example=12000),
                                "notes": openapi.Schema(type=openapi.TYPE_STRING, example="Urgent delivery"),
                                "order_status": openapi.Schema(type=openapi.TYPE_STRING, example="Pending"),
                                "order_items": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "product": openapi.Schema(type=openapi.TYPE_INTEGER, example=4),
                                            "qty": openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                                            "price": openapi.Schema(type=openapi.TYPE_NUMBER, example=100.00),
                                            "tax": openapi.Schema(type=openapi.TYPE_NUMBER, example=100),
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid input or bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Quantity is required."),
                    }
                )
            ),
            404: openapi.Response(
                description="Purchase order not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Purchase order not found."),
                    }
                )
            )
        }
    )
    def put(self, request, order_id):
        try:
            user = request.user
            data = request.data
            items = data.get('items')

            if users_utils.is_required(order_id):
                return Response({
                    "success": False,
                    "message": "Order ID is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if items:
                for item in items:
                    if users_utils.is_required(item.get('qty')):
                        return Response({"success": False, "message": "Quantity is required."}, status=status.HTTP_400_BAD_REQUEST)

                    if not products_models.Products.objects.filter(product_id=item.get('product_id'), user=user, is_deleted=False).exists():
                        return Response({"success": False, "message": "Invalid Product ID."}, status=status.HTTP_400_BAD_REQUEST)

            # Get the purchase order
            purchase_order = products_models.PurchaseOrders.objects.filter(
                order_id=order_id, user=user, is_deleted=False).first()

            if not purchase_order:
                return Response({"success": False, "message": "Purchase order not found."}, status=status.HTTP_404_NOT_FOUND)

            # Update purchase order fields
            serializer = products_serializer.PurchaseOrderSerializer(
                purchase_order, data=data, partial=True)

            if serializer.is_valid():
                order_data = serializer.save()

                if items:
                    for item in items:
                        product_id = item.get('product_id')
                        qty = item.get('qty')
                        tax = item.get('tax', 0)

                        product = products_models.Products.objects.get(
                            product_id=product_id, user=user, is_deleted=False)

                        existing_item = products_models.OrderItems.objects.filter(
                            order=order_data, product=product).first()

                        if existing_item:
                            if existing_item.qty != qty or existing_item.tax != tax:
                                existing_item.qty = qty
                                existing_item.tax = tax
                                existing_item.price = product.selling_price
                                existing_item.save()
                        else:
                            item_data = {
                                'order': order_data.order_id,
                                'product': product.product_id,
                                'qty': qty,
                                'price': product.selling_price,
                                'tax': tax
                            }

                            items_serializer = products_serializer.OrderItemsSeializer(
                                data=item_data)
                            if items_serializer.is_valid():
                                items_serializer.save()
                            else:
                                return Response({"success": False, "error": items_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                order_items = products_models.OrderItems.objects.filter(
                    order=order_data)
                order_items_serializer = products_serializer.OrderItemsSeializer(
                    order_items, many=True).data

                response_data = products_serializer.PurchaseOrderSerializer(
                    order_data).data
                response_data['order_items'] = order_items_serializer

                return Response({
                    "success": True,
                    "message": "Purchase Order updated successfully",
                    "data": response_data
                }, status=status.HTTP_200_OK)

            else:
                return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete Purchase Order",
        operation_description="Delete a specific purchase order and all its associated items for the authenticated user.",
        tags=["Purchase Orders"],
        responses={
            200: openapi.Response(
                description="Purchase order deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Purchase Order Deleted"),
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request (missing or invalid order ID)",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Order ID is required"),
                    }
                )
            ),
            404: openapi.Response(
                description="Purchase order not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Purchase order not found"),
                    }
                )
            )
        }
    )
    def delete(self, request, order_id):
        try:
            user = request.user

            if users_utils.is_required(order_id):
                return Response({
                    "success": False,
                    "message": "Order ID is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            purchase_order = products_models.PurchaseOrders.objects.filter(
                order_id=order_id, user=user, is_deleted=False).first()

            if not purchase_order:
                return Response({
                    "success": False,
                    "message": "Purchase order not found"
                }, status=status.HTTP_404_NOT_FOUND)

            products_models.OrderItems.objects.filter(
                order=purchase_order).delete()

            purchase_order.delete()

            return Response({
                "success": True,
                "message": "Purchase Order Deleted"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = products_serializer.InvoiceSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        invoice_data = products_models.Invoice.objects.filter(
            is_deleted=False).order_by('-created_at')
        response_data = []

        invoice_type = self.request.query_params.get('invoice_type')

        if invoice_type:
            if not invoice_type in ['sales', 'purchase']:
                return Response({"success": False, "message": "Invalid invoice type"}, status=status.HTTP_400_BAD_REQUEST)

            if invoice_type:
                invoice_data = invoice_data.filter(invoice_type=invoice_type)

        for invoice in invoice_data:
            items = products_models.InvoiceItems.objects.filter(
                invoice=invoice)

            total_items = items.count()

            if invoice_type == "sales":
                response_data.append({
                    'invoice_id': invoice.invoice_id,
                    'client': invoice.client.client_name,
                    'invoice_number': invoice.invoice_number,
                    'total_items': total_items,
                    'total_price': invoice.total,
                    'status': invoice.status,
                })

            if invoice_type == "purchase":
                response_data.append({
                    'invoice_id': invoice.invoice_id,
                    'user': invoice.user.fullname,
                    'invoice_number': invoice.invoice_number,
                    'total_items': total_items,
                    'total_price': invoice.total,
                    'status': invoice.status,
                })

        return response_data

    @swagger_auto_schema(
        operation_summary="List Invoices",
        operation_description="Retrieve a paginated list of invoices for the authenticated user, filtered by invoice type (sales or purchase).",
        tags=['Invoices'],
        manual_parameters=[
            openapi.Parameter(
                name='invoice_type',
                in_=openapi.IN_QUERY,
                description="Filter invoices by type: 'sales' for invoices created by the user, 'purchase' for invoices where user is the client",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['sales', 'purchase']
            ),
            openapi.Parameter(
                name='page',
                in_=openapi.IN_QUERY,
                description='Page number for pagination (DRF style)',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                name='page_size',
                in_=openapi.IN_QUERY,
                description='Number of items per page (if supported)',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: openapi.Response(
                description="A paginated list of invoices",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Invoices fetched successfully"),
                        "count": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                        "next": openapi.Schema(type=openapi.FORMAT_URI, example=None),
                        "previous": openapi.Schema(type=openapi.FORMAT_URI, example=None),
                        "results": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "invoice_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                    "invoice_number": openapi.Schema(type=openapi.TYPE_STRING, example="INV-2025-01"),
                                    # both client and user are included depending on invoice_type
                                    "client": openapi.Schema(type=openapi.TYPE_STRING, example="Acme Corp"),
                                    "user": openapi.Schema(type=openapi.TYPE_STRING, example="Alice Smith"),
                                    "total_items": openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                                    "total_price": openapi.Schema(type=openapi.TYPE_STRING, example="150.00"),
                                }
                            )
                        )
                    }
                ),
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Invoices fetched successfully",
                        "count": 1,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "invoice_id": 1,
                                "invoice_number": "INV-2025-01",
                                "client": "Acme Corp",
                                "total_items": 3,
                                "total_price": "150.00"
                            }
                        ]
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Invalid invoice type"),
                    }
                )
            )
        }
    )
    def get(self, request):
        try:
            response_data = self.get_queryset()
            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(
                response_data, request)

            return paginator.get_paginated_response(result_page)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AddInvoiceView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = products_serializer.InvoiceSerializer

    @swagger_auto_schema(
        operation_summary="Add Invoice",
        operation_description="Create an invoice for the authenticated user along with its line items.",
        tags=['Invoices'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['client', 'items'],
            properties={
                'client': openapi.Schema(type=openapi.TYPE_INTEGER, description='Client ID'),
                'invoice_number': openapi.Schema(type=openapi.TYPE_STRING, description='Invoice number'),
                'issue_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'payment_due': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'subtotal': openapi.Schema(type=openapi.TYPE_NUMBER),
                'tax': openapi.Schema(type=openapi.TYPE_NUMBER),
                'discount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'total': openapi.Schema(type=openapi.TYPE_NUMBER),
                'notes': openapi.Schema(type=openapi.TYPE_STRING),
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING),
                'items': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['product_id', 'qty'],
                        properties={
                            'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
                            'qty': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity'),
                            'price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Unit price'),
                            'discount_amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'tax': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'gst_category': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'is_inter_state_sale': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'weight_based_item': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        }
                    )
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Invoice created successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Purchase Order Created Successfully'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'invoice_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'invoice_number': openapi.Schema(type=openapi.TYPE_STRING, example='INV-2025-01'),
                                'user': openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                                'client': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                                'subtotal': openapi.Schema(type=openapi.TYPE_NUMBER, example=100.00),
                                'tax': openapi.Schema(type=openapi.TYPE_NUMBER, example=10.00),
                                'total': openapi.Schema(type=openapi.TYPE_NUMBER, example=110.00),
                                'order_items': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'item_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                            'invoice': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                            'product': openapi.Schema(type=openapi.TYPE_INTEGER, example=4),
                                            'qty': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                                            'price': openapi.Schema(type=openapi.TYPE_NUMBER, example='50.00'),
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description='Bad request',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Client ID is required'),
                        'error': openapi.Schema(type=openapi.TYPE_OBJECT, example={})
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            user = request.user
            data = request.data
            client = data.get('client')
            items = data.get('items')
            invoice_type = data.get('invoice_type')

            if users_utils.is_required(client):
                return Response({"success": False, "message": "Client ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(invoice_type):
                return Response({"success": False, "message": "Invoice type is required"}, status=status.HTTP_400_BAD_REQUEST)

            if invoice_type and invoice_type not in ["purchase", "sales"]:
                return Response({"success": False, "message": "Invalid invoice type"}, status=status.HTTP_400_BAD_REQUEST)

            if items:
                for item in items:
                    if users_utils.is_required(item.get('qty')):
                        return Response({"success": False, "message": "Quantity is required."}, status=status.HTTP_400_BAD_REQUEST)

                    if not products_models.Products.objects.filter(product_id=item.get('product_id'), user=user, is_deleted=False).exists():
                        return Response({"success": False, "message": "Invalid Product ID."}, status=status.HTTP_400_BAD_REQUEST)

            # if data.get('invoice_type') and data.get('invoice_type') == "purchase":
            #     if data.get('payment_method') in ['card', 'upi']:
            #         data['status'] = "Paid"

            data['user'] = user.user_id
            serializer = self.serializer_class(data=data)

            if serializer.is_valid():
                invoice_instance = serializer.save()

                if items:
                    item_list = []
                    for item in items:
                        product = products_models.Products.objects.get(
                            product_id=item.get('product_id'), user=user, is_deleted=False)

                        item_data = {
                            'invoice': invoice_instance.invoice_id,
                            'product': product.product_id,
                            'qty': item.get('qty'),
                            'price': item.get('price'),
                            'discount_amount': item.get('discount_amount'),
                            'tax': item.get('tax'),
                            'gst_category': item.get('gst_category'),
                            'is_inter_state_sale': item.get('is_inter_state_sale'),
                            'weight_based_item': item.get('weight_based_item')
                        }

                        items_serializer = products_serializer.InvoiceItemsSerializer(
                            data=item_data)
                        if items_serializer.is_valid():
                            items_serializer.save()
                            item_list.append(items_serializer.data)
                        else:
                            return Response({"success": False, "error": items_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                products_models.ActivityLog.objects.create(
                    user=user,
                    action="purchase_order" if invoice_type == "purchase" else "sales_order",
                    title=f"{'Purchase' if invoice_type == 'purchase' else 'Sales'} Order Created - {invoice_instance.invoice_number}",
                    description=f"New {'Purchase' if invoice_type == 'purchase' else 'Sales'} Order Created - {invoice_instance.invoice_number} from {invoice_instance.client.client_name}",
                    extra_data={
                        "invoice_id": invoice_instance.invoice_id,
                        "amount": float(invoice_instance.total),
                    },
                )

                response_data = self.serializer_class(invoice_instance).data
                response_data['order_items'] = item_list

                return Response({"success": True, "message": "Purchase Order Created Successfully", "data": response_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Invoice Detail",
        operation_description="Retrieve the details of a specific invoice by ID for the authenticated user.",
        tags=["Invoices"],
        parameters=[
            openapi.Parameter(
                'invoice_id', openapi.IN_PATH, description="ID of the invoice to fetch",
                type=openapi.TYPE_INTEGER, required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="Invoice details fetched successfully",
                schema=products_serializer.InvoiceDetailsSerializer,
            ),
            400: openapi.Response(
                description="Bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
            404: openapi.Response(
                description="Invoice not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
        }
    )
    def get(self, request, invoice_id):
        try:
            user = request.user

            if users_utils.is_required(invoice_id):
                return Response({
                    "success": False,
                    "message": "Invoice ID is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            invoice = products_models.Invoice.objects.prefetch_related(
                'invoice_items'
            ).filter(invoice_id=invoice_id, user=user, is_deleted=False).first()

            if not invoice:
                return Response({
                    "success": False,
                    "message": "No invoice found for the given ID"
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = products_serializer.InvoiceDetailsSerializer(
                invoice)
            return Response({
                "success": True,
                "message": "Invoice Details Fetched",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update Invoice",
        operation_description="Update an existing invoice and its line items for the authenticated user.",
        tags=["Invoices"],
        request_body=products_serializer.InvoiceSerializer,
        parameters=[
            openapi.Parameter(
                'invoice_id', openapi.IN_PATH, description="ID of the invoice to update",
                type=openapi.TYPE_INTEGER, required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="Invoice updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                ),
            ),
            400: openapi.Response(
                description="Invalid input or bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'error': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                ),
            ),
            404: openapi.Response(
                description="Invoice not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
        }
    )
    def put(self, request, invoice_id):
        try:
            user = request.user
            data = request.data
            items = data.get('items')

            if users_utils.is_required(invoice_id):
                return Response({
                    "success": False,
                    "message": "Invoice ID is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if items:
                for item in items:
                    if users_utils.is_required(item.get('qty')):
                        return Response({"success": False, "message": "Quantity is required."}, status=status.HTTP_400_BAD_REQUEST)

                    if not products_models.Products.objects.filter(product_id=item.get('product_id'), user=user, is_deleted=False).exists():
                        return Response({"success": False, "message": "Invalid Product ID."}, status=status.HTTP_400_BAD_REQUEST)

            # Get the purchase order
            invoice = products_models.Invoice.objects.filter(
                invoice_id=invoice_id, user=user, is_deleted=False).first()

            if not invoice:
                return Response({"success": False, "message": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

            # Update purchase order fields
            serializer = products_serializer.InvoiceSerializer(
                invoice, data=data, partial=True)

            if serializer.is_valid():
                invoice_data = serializer.save()

                if items:
                    for item in items:
                        product_id = item.get('product_id')
                        qty = item.get('qty')
                        tax = item.get('tax', 0)
                        unit_of_measurement = item.get('unit_of_measurement')
                        gst_category = item.get('gst_category')
                        price = item.get('price')
                        discount_amount = item.get('discount_amount')
                        is_inter_state_sale = item.get('is_inter_state_sale')
                        weight_based_item = item.get('weight_based_item')

                        product = products_models.Products.objects.get(
                            product_id=product_id, user=user, is_deleted=False)

                        existing_item = products_models.InvoiceItems.objects.filter(
                            invoice=invoice_data, product=product).first()

                        if existing_item:
                            updated = False
                            new_values = {
                                'qty': qty,
                                'tax': tax,
                                'price': price,
                                'unit_of_measurement': unit_of_measurement,
                                'gst_category': gst_category,
                                'discount_amount': discount_amount,
                                'is_inter_state_sale': is_inter_state_sale,
                                'weight_based_item': weight_based_item,
                            }

                            for attr, new_val in new_values.items():
                                if getattr(existing_item, attr) != new_val:
                                    setattr(existing_item, attr, new_val)
                                    updated = True

                            if updated:
                                existing_item.save()
                        else:
                            item_data = {
                                'invoice': invoice_data.invoice_id,
                                'product': product.product_id,
                                'qty': qty,
                                'price': price,
                                'tax': tax,
                                'unit_of_measurement': unit_of_measurement,
                                'gst_category': gst_category,
                                'discount_amount': discount_amount,
                                'is_inter_state_sale': is_inter_state_sale,
                                'weight_based_item': weight_based_item
                            }

                            items_serializer = products_serializer.InvoiceItemsSerializer(
                                data=item_data)
                            if items_serializer.is_valid():
                                items_serializer.save()
                            else:
                                return Response({"success": False, "error": items_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                invoice_items = products_models.InvoiceItems.objects.filter(
                    invoice=invoice_data)
                invoice_items_serializer = products_serializer.InvoiceItemsSerializer(
                    invoice_items, many=True).data

                response_data = products_serializer.InvoiceSerializer(
                    invoice_data).data
                response_data['invoice_items'] = invoice_items_serializer

                return Response({
                    "success": True,
                    "message": "Invoice updated successfully",
                    "data": response_data
                }, status=status.HTTP_200_OK)

            else:
                return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete Invoice",
        operation_description="Delete a specific invoice and all its associated items for the authenticated user.",
        tags=["Invoices"],
        parameters=[
            openapi.Parameter(
                'invoice_id', openapi.IN_PATH, description="ID of the invoice to delete",
                type=openapi.TYPE_INTEGER, required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="Invoice deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
            400: openapi.Response(
                description="Bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
            404: openapi.Response(
                description="Invoice not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
        }
    )
    def delete(self, request, invoice_id):
        try:
            user = request.user

            if users_utils.is_required(invoice_id):
                return Response({
                    "success": False,
                    "message": "Invoice ID is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            invoice = products_models.Invoice.objects.filter(
                invoice_id=invoice_id, user=user, is_deleted=False).first()

            if not invoice:
                return Response({
                    "success": False,
                    "message": "Inivoice not found"
                }, status=status.HTTP_404_NOT_FOUND)

            products_models.InvoiceItems.objects.filter(
                invoice=invoice).delete()

            invoice.delete()

            return Response({
                "success": True,
                "message": "Invoice Deleted"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HomePageView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Home Page Totals",
        operation_description=(
            "Return aggregated totals for the authenticated user's dashboard: "
            "total sales, total purchases, profit, expenses, pending payments and overdue invoices."
        ),
        tags=["Dashboard"],
        responses={
            200: openapi.Response(
                description="Home page totals fetched",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'total_sales': openapi.Schema(type=openapi.TYPE_STRING, example='1000.00'),
                                'total_purchase': openapi.Schema(type=openapi.TYPE_STRING, example='500.00'),
                                'profit': openapi.Schema(type=openapi.TYPE_STRING, example='500.00'),
                                'expenses': openapi.Schema(type=openapi.TYPE_STRING, example='100.00'),
                                'pending_payments': openapi.Schema(type=openapi.TYPE_STRING, example='200.00'),
                                'overdue_invoices': openapi.Schema(type=openapi.TYPE_STRING, example='50.00'),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        }
    )
    def get(self, request):
        try:
            user = request.user
            # Total sales: sum of invoice.total for this user
            total_sales_agg = products_models.Invoice.objects.filter(
                user=user, invoice_type="sales", is_deleted=False).aggregate(total=Sum('total'))
            total_sales = total_sales_agg.get('total') or Decimal('0.00')

            # Total purchases: sum of purchase orders total for this user
            total_purchase_agg = products_models.PurchaseOrders.objects.filter(
                user=user, order_type="purchase", is_deleted=False).aggregate(total=Sum('total'))
            total_purchase = total_purchase_agg.get('total') or Decimal('0.00')

            # Profit: use invoice items to compute (price - cost_price) * qty where possible
            profit = Decimal('0.00')
            invoice_items_qs = products_models.InvoiceItems.objects.select_related('product', 'invoice').filter(
                invoice__user=user, invoice__is_deleted=False
            )

            for item in invoice_items_qs:
                qty = Decimal(item.qty or 0)
                price = Decimal(item.price or 0)
                cost_price = Decimal(
                    getattr(item.product, 'cost_price', 0) or 0)
                profit += (price - cost_price) * qty

            # Pending payments: invoices with a payment_due in the future or today (no payment tracking exists)
            today = timezone.localdate()
            pending_agg = products_models.Invoice.objects.filter(
                user=user, invoice_type="sales", is_deleted=False, payment_due__isnull=False, payment_due__gte=today).aggregate(total=Sum('total'))
            pending_payments = pending_agg.get('total') or Decimal('0.00')

            # Overdue invoices: payment_due before today
            overdue_agg = products_models.Invoice.objects.filter(
                user=user, invoice_type="purchase", is_deleted=False, payment_due__isnull=False, payment_due__lt=today).aggregate(total=Sum('total'))
            overdue_invoices_total = overdue_agg.get(
                'total') or Decimal('0.00')

            overdue_invoices = products_models.Invoice.objects.filter(
                user=user, invoice_type="purchase", status="Pending", is_deleted=False, payment_due__isnull=False, payment_due__lt=today)

            for invoice in overdue_invoices:
                products_models.ActivityLog.objects.create(
                    user=user,
                    action="invoice_overdue",
                    title="Invoice Reminder",
                    description=f"invoice #{invoice.invoice_number} due soon",
                    extra_data={
                        "invoice_id": invoice.invoice_id,
                        "amount": float(invoice.total),
                    },
                )

                invoice.status = "Overdue"
                invoice.save()

            recent_logs = products_models.ActivityLog.objects.filter(
                user=user).order_by('-created_at')[:5]

            recent_logs_serializer = products_serializer.ActivityLogSerializer(
                recent_logs, many=True).data

            # Expenses: no Expense model present in this project; return 0.00 for now.
            expenses = Decimal('0.00')

            data = {
                "total_sales": str(total_sales),
                "total_purchase": str(total_purchase),
                "profit": str(profit),
                "expenses": str(expenses),
                "pending_payments": str(pending_payments),
                "overdue_invoices": str(overdue_invoices_total),
                "recent_logs": recent_logs_serializer,
            }

            return Response({"success": True, "message": "Home page totals fetched", "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateInvoiceStatus(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update Invoice Status",
        operation_description="Update the status of an invoice for the authenticated user.",
        tags=['Invoices'],
        manual_parameters=[
            openapi.Parameter(
                name='invoice_id',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                required=True,
                description='ID of the invoice to update'
            ),
            openapi.Parameter(
                name='status',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='New status for the invoice'
            ),
        ],
        responses={
            200: openapi.Response(
                description="Invoice status updated successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Invoice status updated successfully"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Missing or invalid parameters"
                    }
                }
            ),
            404: openapi.Response(
                description="Invoice not found",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Invoice not found"
                    }
                }
            ),
        }
    )
    def get(self, request, invoice_id):
        try:
            user = request.user
            status_value = request.query_params.get('status')

            if users_utils.is_required(invoice_id):
                return Response({"success": False, "message": "Invoice ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(status_value):
                return Response({"success": False, "message": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)

            invoice = products_models.Invoice.objects.filter(
                invoice_id=invoice_id, user=user, is_deleted=False).first()

            if not invoice:
                return Response({"success": False, "message": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

            invoice.status = status_value
            invoice.save()

            return Response({"success": True, "message": "Invoice status updated successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateOrderStatus(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update Order Status",
        operation_description="Update the status of an order for the authenticated user.",
        tags=["Purchase Orders"],
        manual_parameters=[
            openapi.Parameter(
                name="order_id",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                required=True,
                description="Order ID of the purchase order"
            ),
            openapi.Parameter(
                name="status",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description="New status value for the order"
            ),
        ],
        responses={
            200: openapi.Response(
                description="Order status updated successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Order status updated successfully"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Missing or invalid parameters"
                    }
                }
            ),
            404: openapi.Response(
                description="Order not found",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Order not found"
                    }
                }
            ),
        }
    )
    def get(self, request, order_id):
        try:
            user = request.user
            status_value = request.query_params.get('status')

            if users_utils.is_required(order_id):
                return Response({"success": False, "message": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(status_value):
                return Response({"success": False, "message": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)

            invoice = products_models.PurchaseOrders.objects.filter(
                order_id=order_id, user=user, is_deleted=False).first()

            if not invoice:
                return Response({"success": False, "message": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

            invoice.order_status = status_value
            invoice.save()

            return Response({"success": True, "message": "Order status updated successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
