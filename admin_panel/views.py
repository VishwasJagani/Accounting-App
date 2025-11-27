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
from users import models as users_models
from users import serializer as users_serializer
from admin_panel import serializer as admin_serializer


class AdminRegisterView(APIView):

    def post(self, request):
        try:
            data = request.data
            # user_role = data.get('user_role')
            fullname = data.get('fullname')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')

            # if users_utils.is_required(user_role):
            #     return Response({"success": False, "message": "User role is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(fullname):
                return Response({"success": False, "message": "Fullname is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(email):
                return Response({"success": False, "message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(password):
                return Response({"success": False, "message": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)

            if len(password) < 8:
                return Response({"success": False, "message": "Password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

            if password != confirm_password:
                return Response({"success": False, "message": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

            if users_models.User.objects.filter(email=email, is_active=True, is_deleted=False).exists():
                return Response({"success": False, "message": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

            data['user_role'] = 1
            data['is_admin'] = True
            serializer = users_serializer.UserSerializer(data=data)

            if serializer.is_valid():
                user = serializer.save()

                token = users_utils.get_user_token(user)

                user_data = serializer.data
                user_data['token'] = token['access']

                return Response({"success": True, "message": "Admin registered successfully.", "data": user_data}, status=status.HTTP_200_OK)

            else:
                return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = admin_serializer.AdminUserListSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        search_params = self.request.query_params.get('search')
        user_status = self.request.query_params.get('active')

        users = users_models.User.objects.filter(is_deleted=False).exclude(
            is_admin=True).order_by('-created_at')

        if search_params:
            users = users.filter(Q(email__icontains=search_params) | Q(
                fullname__icontains=search_params))

        if user_status:
            if user_status == 'true':
                users = users.filter(is_active=True)

        serializer = self.serializer_class(users, many=True)
        return serializer.data

    @swagger_auto_schema(
        operation_summary="List All Users (Admin Only)",
        operation_description=(
            "Retrieves a paginated list of all non-admin users. "
            "Supports filtering by name/email (`search`) and active status (`active=true`). "
            "Only users with the 'admin' role are allowed to access this endpoint."
        ),
        tags=['Admin - User Management'],
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search by email or full name (case-insensitive).",
                type=openapi.TYPE_STRING,
                required=False,
                example="john"
            ),
            openapi.Parameter(
                'active',
                openapi.IN_QUERY,
                description="Filter users by active status. Use 'true' to get only active users.",
                type=openapi.TYPE_STRING,
                enum=['true', 'false'],
                required=False,
                example="true"
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number for pagination.",
                type=openapi.TYPE_INTEGER,
                required=False,
                example=1
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Number of results per page.",
                type=openapi.TYPE_INTEGER,
                required=False,
                example=10
            ),
        ],
        responses={
            200: openapi.Response(
                description="User list retrieved successfully.",
                examples={
                    "application/json": {
                        "count": 25,
                        "next": "https://api.example.com/api/admin/users/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "user_id": 101,
                                "fullname": "John Doe",
                                "email": "john.doe@example.com",
                                "is_active": True,
                                "created_at": "2025-06-10T09:45:32Z",
                                "role": "client"
                            },
                            {
                                "user_id": 102,
                                "fullname": "Jane Smith",
                                "email": "jane.smith@example.com",
                                "is_active": False,
                                "created_at": "2025-05-28T12:14:10Z",
                                "role": "supplier"
                            }
                        ]
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized — only admins can access this endpoint.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Only Admins Are Allowed."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request — unexpected error occurred.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "An unexpected error occurred."
                    }
                }
            ),
        }
    )
    def get(self, request):
        try:
            user = request.user

            if not user.user_role.role_name == "admin":
                return Response({"success": False, "message": "Only Admins Are Allowed."}, status=status.HTTP_401_UNAUTHORIZED)

            queryset = self.get_queryset()
            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(queryset, request)
            return paginator.get_paginated_response(result_page)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get User Details by ID (Admin Only)",
        operation_description=(
            "Retrieves detailed information for a specific user identified by `user_id`. "
            "Only users with the 'admin' role are allowed to access this endpoint."
        ),
        tags=['Admin - User Management'],
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="Unique ID of the user to retrieve details for.",
                type=openapi.TYPE_INTEGER,
                required=True,
                example=101
            )
        ],
        responses={
            200: openapi.Response(
                description="User details fetched successfully.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "User Data Is Fetched",
                        "data": {
                            "user_id": 101,
                            "fullname": "John Doe",
                            "email": "john.doe@example.com",
                            "phone_number": "+1-555-9876",
                            "is_active": True,
                            "created_at": "2025-06-10T09:45:32Z",
                            "role": "client",
                            "company": {
                                "company_name": "TechCorp Solutions",
                                "registration_number": "TC1234567",
                                "business_type": "Manufacturing"
                            }
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request — invalid or missing parameters.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "User Id is required."
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized — only admins can access this endpoint.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Only Admins Are Allowed."
                    }
                }
            ),
            404: openapi.Response(
                description="User not found.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "User not found"
                    }
                }
            ),
        }
    )
    def get(self, request, user_id):
        try:
            user = request.user

            if not user.user_role.role_name == "admin":
                return Response({"success": False, "message": "Only Admins Are Allowed."}, status=status.HTTP_401_UNAUTHORIZED)

            if users_utils.is_required(user_id):
                return Response({"success": False, "message": "User Id is required."}, status=status.HTTP_400_BAD_REQUEST)

            user_obj = users_models.User.objects.filter(
                user_id=user_id).first()

            if not user_obj:
                return Response({"success": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = users_serializer.UserSerializer(user_obj).data

            return Response({"success": True, "message": "User Data Is Fetched", "data": serializer}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update User Details by ID (Admin Only)",
        operation_description=(
            "Allows an admin to update user details by specifying the `user_id`. "
            "Supports partial updates — only provided fields will be modified. "
            "Ensures email uniqueness across active users."
        ),
        tags=['Admin - User Management'],
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="Unique ID of the user to update.",
                type=openapi.TYPE_INTEGER,
                required=True,
                example=101
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'fullname': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Full name of the user.",
                    example="John Doe"
                ),
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='email',
                    description="Email address of the user. Must be unique.",
                    example="john.doe@example.com"
                ),
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User's contact number.",
                    example="+1-555-9876"
                ),
                'is_active': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Set to `true` to activate or `false` to deactivate the user.",
                    example=True
                ),
                'role': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Role assigned to the user (e.g., 'client', 'supplier').",
                    example="client"
                ),
                'company_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the company the user is associated with.",
                    example=15
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="User updated successfully.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "User updated successfully.",
                        "data": {
                            "user_id": 101,
                            "fullname": "John Doe",
                            "email": "john.doe@example.com",
                            "phone_number": "+1-555-9876",
                            "is_active": True,
                            "role": "client",
                            "updated_at": "2025-10-27T12:30:15Z"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request — invalid or duplicate data.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Email already exists."
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized — only admins can access this endpoint.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Only Admins Are Allowed."
                    }
                }
            ),
            404: openapi.Response(
                description="User not found.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "User not found"
                    }
                }
            ),
        }
    )
    def put(self, request, user_id):
        try:
            user = request.user
            data = request.data
            email = data.get('email')

            if not user.user_role.role_name == "admin":
                return Response({"success": False, "message": "Only Admins Are Allowed."}, status=status.HTTP_401_UNAUTHORIZED)

            if users_utils.is_required(user_id):
                return Response({"success": False, "message": "User Id is required"}, status=status.HTTP_400_BAD_REQUEST)

            user_obj = users_models.User.objects.filter(
                user_id=user_id).first()

            if not user_obj:
                return Response({"success": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            if email:
                if users_models.User.objects.filter(email=email, is_active=True, is_deleted=False).exclude(user_id=user_id).exists():
                    return Response({"success": False, "message": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = users_serializer.UserSerializer(
                instance=user_obj, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "User updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

            return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete User by ID (Admin Only)",
        operation_description=(
            "Allows an admin to delete a user by specifying the `user_id`. "
            "If the user has a profile image, it will also be removed from the server."
        ),
        tags=['Admin - User Management'],
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_PATH,
                description="Unique ID of the user to delete.",
                type=openapi.TYPE_INTEGER,
                required=True,
                example=101
            ),
        ],
        responses={
            200: openapi.Response(
                description="User deleted successfully.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "User deleted successfully."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request — missing or invalid parameters.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "User Id is required"
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized — only admins can access this endpoint.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Only Admins Are Allowed."
                    }
                }
            ),
            404: openapi.Response(
                description="User not found.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "User not found"
                    }
                }
            ),
        }
    )
    def delete(self, request, user_id):
        try:
            user = request.user

            if not user.user_role.role_name == "admin":
                return Response({"success": False, "message": "Only Admins Are Allowed."}, status=status.HTTP_401_UNAUTHORIZED)

            if users_utils.is_required(user_id):
                return Response({"success": False, "message": "User Id is required"}, status=status.HTTP_400_BAD_REQUEST)

            user_obj = users_models.User.objects.filter(
                user_id=user_id, is_deleted=False).first()

            if not user_obj:
                return Response({"success": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            if user_obj.profile_image:
                os.remove(user_obj.profile_image.path)

            user_obj.delete()

            return Response({"success": True, "message": "User deleted successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
