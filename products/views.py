# Django
import os
from drf_yasg import openapi
from django.db.models import Q
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
            user=user, is_deleted=False)

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
            queryset = self.get_queryset(request)
            serializer = self.serializer_class(queryset, many=True)
            return Response({"success": True, "message": "Product Data Fetched", "data": serializer.data}, status=status.HTTP_200_OK)
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
                                'stock_level': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'reorder_point': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'selling_price': openapi.Schema(type=openapi.TYPE_STRING),
                                'cost_price': openapi.Schema(type=openapi.TYPE_STRING),
                                'tax': openapi.Schema(type=openapi.TYPE_STRING),
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
