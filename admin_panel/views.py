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
