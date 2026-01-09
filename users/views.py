# Django
import os
from decimal import Decimal
from drf_yasg import openapi
from django.db.models import Q, Sum, F, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta, datetime
import calendar
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.hashers import check_password

# Rest FrameWork
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response

# Local
from users import models as users_models
from users import serializer as users_serializer
from users import utils as users_utils
from products import models as products_models
from products import serializer as products_serializer
from base_files.base_permission import IsAuthenticated
from base_files.base_pagination import CustomPagination
from base_files.base_task import send_mail


class RoleList(generics.ListAPIView):
    queryset = users_models.RoleModel.objects.all().exclude(role_name="admin")
    serializer_class = users_serializer.RoleSerializer

    @swagger_auto_schema(
        operation_summary="Get all roles (except admin)",
        operation_description="Retrieve a list of roles available for users (excluding the admin role).",
        tags=["Auth"],
        responses={
            200: openapi.Response(
                description="Roles retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Roles retrieved successfully.",
                        "data": [
                            {"id": 1, "role_name": "customer"},
                            {"id": 2, "role_name": "manager"}
                        ]
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Some error occurred."
                    }
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(
                {
                    "success": True,
                    "message": "Roles retrieved successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RegisterView(APIView):
    """
    View for registering a new user.
    """
    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Creates a new user account after validating input fields",
        tags=["Auth"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["user_role", "fullname", "email",
                      "password", "confirm_password", "phone_number"],
            properties={
                'user_role': openapi.Schema(type=openapi.TYPE_STRING, description="Role of the user (e.g., admin, customer)"),
                'fullname': openapi.Schema(type=openapi.TYPE_STRING, description="Full name of the user"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Email address"),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Phone number"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description="Password (min 8 characters)"),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description="Confirm password"),
            },
        ),
        responses={
            200: openapi.Response(
                description="User registered successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "User registered successfully.",
                        "data": {
                            "id": 1,
                            "fullname": "John Doe",
                            "email": "john@example.com",
                            "phone_number": "9876543210",
                            "token": "jwt-access-token"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request (validation failed)",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Email already exists."
                    }
                }
            ),
        },
    )
    def post(self, request):
        try:
            data = request.data
            # user_role = data.get('user_role')
            fullname = data.get('fullname')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')
            phone_number = data.get('phone_number')
            device = data.get('device', None)
            ip_address = data.get('ip_address', None)
            state = data.get('state', None)
            country = data.get('country', None)

            # if users_utils.is_required(user_role):
            #     return Response({"success": False, "message": "User role is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(fullname):
                return Response({"success": False, "message": "Fullname is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(email):
                return Response({"success": False, "message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(phone_number):
                return Response({"success": False, "message": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(password):
                return Response({"success": False, "message": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)

            if len(password) < 8:
                return Response({"success": False, "message": "Password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

            if password != confirm_password:
                return Response({"success": False, "message": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

            if users_models.User.objects.filter(email=email, is_active=True, is_deleted=False).exists():
                return Response({"success": False, "message": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

            data['user_role'] = 2
            data['last_login'] = timezone.now()
            serializer = users_serializer.UserSerializer(data=data)

            if serializer.is_valid():
                user = serializer.save()

                token = users_utils.get_user_token(user)

                user_data = serializer.data
                user_data['token'] = token['access']

                login_data = {
                    "user": user_data.get('user_id'),
                    "login_time": timezone.now(),
                    "device": device,
                    "ip_address": ip_address,
                    "state": state,
                    "country": country,
                }

                login_data_serializer = users_serializer.UserLoginSerializer(
                    data=login_data)

                if login_data_serializer.is_valid():
                    login_data_serializer.save()

                return Response({"success": True, "message": "User registered successfully.", "data": user_data}, status=status.HTTP_200_OK)

            else:
                return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    View for logging in a user.
    """
    @swagger_auto_schema(
        operation_summary="Login a user",
        operation_description="Authenticate user with email and password. Returns JWT token if successful.",
        tags=["Auth"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="User's email"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description="User's password"),
                'is_admin': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Login as admin (optional, default False)"),
            },
        ),
        responses={
            200: openapi.Response(
                description="User logged in successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "User logged in successfully.",
                        "data": {
                            "id": 1,
                            "fullname": "John Doe",
                            "email": "john@example.com",
                            "phone_number": "9876543210",
                            "token": "jwt-access-token"
                        }
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized (wrong credentials)",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Invalid password."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Email is required."
                    }
                }
            ),
        }
    )
    def post(self, request):
        try:
            data = request.data
            email = data.get('email')
            password = data.get('password')
            is_admin = data.get('is_admin', False)
            device = data.get('device', None)
            ip_address = data.get('ip_address', None)
            state = data.get('state', None)
            country = data.get('country', None)

            if users_utils.is_required(email):
                return Response({"success": False, "message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(password):
                return Response({"success": False, "message": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)

            if is_admin:
                user = users_models.User.objects.filter(
                    email=email, is_admin=True, is_active=True, is_deleted=False).first()
            else:
                user = users_models.User.objects.filter(
                    email=email, is_admin=False, is_active=True, is_deleted=False).first()

            if user:
                if check_password(password, user.password):
                    token = users_utils.get_user_token(user)
                    user.last_login = timezone.now()
                    user.save()

                    login_data = {
                        "user": user.user_id,
                        "login_time": timezone.now(),
                        "device": device,
                        "ip_address": ip_address,
                        "state": state,
                        "country": country,
                    }

                    login_data_serializer = users_serializer.UserLoginSerializer(
                        data=login_data)

                    if login_data_serializer.is_valid():
                        login_data_serializer.save()

                    user_data = users_serializer.UserSerializer(user).data
                    user_data['token'] = token['access']
                    return Response({"success": True, "message": "User logged in successfully.", "data": user_data}, status=status.HTTP_200_OK)

                else:
                    return Response({"success": False, "message": "Invalid password."}, status=status.HTTP_401_UNAUTHORIZED)

            else:
                return Response({"success": False, "message": "User not found."}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    View for retrieving and updating a user's profile.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get logged-in user's profile",
        operation_description="Retrieve profile information of the authenticated user.",
        tags=["User"],
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT access token. Format: Bearer <token>",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="Profile retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "User profile retrieved successfully.",
                        "data": {
                            "id": 1,
                            "fullname": "John Doe",
                            "email": "john@example.com",
                            "phone_number": "9876543210",
                            "user_role": "customer"
                        }
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized (missing or invalid token)",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
        }
    )
    def get(self, request):
        try:
            user = request.user
            serializer = users_serializer.UserSerializer(user)
            company_obj = users_models.UserCompany.objects.filter(
                user=user, is_deleted=False).first()
            comapny_serializer = users_serializer.UserCompanySerializer(
                company_obj).data
            response_data = {
                "user_data": serializer.data,
                "company_data": comapny_serializer,
            }
            return Response({"success": True, "message": "User profile retrieved successfully.", "data": response_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update User Profile",
        operation_description="Allows the authenticated user to update their profile details.",
        tags=['User'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'fullname': openapi.Schema(type=openapi.TYPE_STRING, description='Full name of the user'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Email address'),
                'country_code': openapi.Schema(type=openapi.TYPE_STRING, description='Country code (e.g., +91)'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
                'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Date of birth (YYYY-MM-DD)'),
                'profile_image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY, description='Profile image file'),
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='Home address'),
                'work_address': openapi.Schema(type=openapi.TYPE_STRING, description='Work address'),
            },
            required=[],
        ),
        responses={
            200: openapi.Response(
                description="User profile updated successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "User profile updated successfully.",
                        "data": {
                            "user_id": 1,
                            "fullname": "John Doe",
                            "email": "johndoe@example.com",
                            "phone_number": "9876543210",
                            "country_code": "+91",
                            "date_of_birth": "1995-05-10",
                            "profile_image": "http://example.com/media/user_profile/john.png",
                            "address": "Home address",
                            "work_address": "Office address",
                            "is_active": True,
                            "is_email_verified": False,
                            "is_phone_verified": False,
                            "is_admin": False
                        }
                    }
                },
            ),
            400: openapi.Response(
                description="Validation error or duplicate email",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "This Email already exists."
                    }
                },
            ),
        },
    )
    def put(self, request):
        try:
            user = request.user
            data = request.data
            email = data.get('email')
            profile_image = data.get('profile_image')

            if email:
                if email != user.email:
                    if users_models.User.objects.filter(email=email, is_deleted=False).exists():
                        return Response({"success": False, "message": "This Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

            if profile_image:
                if not users_utils.is_valid_image(profile_image):
                    return Response({"success": False, "message": "Please Select Valid Image."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = users_serializer.UserSerializer(
                user, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "User profile updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

            else:
                return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete authenticated user",
        operation_description="Deletes User Account Permanently.",
        tags=['User'],
        responses={
            200: openapi.Response(
                description="User deleted successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "User deleted successfully."
                    }
                }
            ),
            400: openapi.Response(
                description="Deletion failed due to error",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Error message"
                    }
                }
            ),
        }
    )
    def delete(self, request):
        try:
            user = request.user

            if user.profile_image:
                if os.path.isfile(user.profile_image.path):
                    os.remove(user.profile_image.path)

            user.delete()

            return Response({"success": True, "message": "User deleted successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    View for changing a user's password.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Change user password",
        operation_description="Allows an authenticated user to change their password by providing the old password, new password, and confirming the new password.",
        tags=['Auth'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['old_password', 'new_password', 'confirm_password'],
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='Current password'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='New password (min 8 characters)'),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='Confirmation of the new password'),
            },
        ),
        responses={
            200: openapi.Response(description='Password changed successfully', examples={
                "application/json": {
                    "success": True,
                    "message": "Password changed successfully."
                }
            }),
            400: openapi.Response(description='Bad request', examples={
                "application/json": {
                    "success": False,
                    "message": "Old password is incorrect."
                }
            }),
        }
    )
    def post(self, request):
        try:
            user = request.user
            data = request.data
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')

            if users_utils.is_required(old_password):
                return Response({"success": False, "message": "Old password is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(new_password):
                return Response({"success": False, "message": "New password is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(confirm_password):
                return Response({"success": False, "message": "Confirm password is required."}, status=status.HTTP_400_BAD_REQUEST)

            if len(new_password) < 8:
                return Response({"success": False, "message": "New password should be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

            if new_password != confirm_password:
                return Response({"success": False, "message": "Confirm password does not match."}, status=status.HTTP_400_BAD_REQUEST)

            if user:
                if not check_password(old_password, user.password):
                    return Response({"success": False, "message": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

                if check_password(new_password, user.password):
                    return Response({"success": False, "message": "New password should not be the same as the old password."}, status=status.HTTP_400_BAD_REQUEST)

                serializer = users_serializer.UserSerializer(
                    user, data={"password": new_password}, partial=True)

                if serializer.is_valid():
                    serializer.save()
                    return Response({"success": True, "message": "Password changed successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SendOTPView(APIView):
    """
    View for sending OTP to a user's registered email address.
    """

    @swagger_auto_schema(
        operation_summary="Send OTP",
        operation_description="Send OTP to the user's email address.",
        tags=['Auth'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email address'),
                'otp_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of OTP request (e.g., reset_password, verify_email)')
            },
            required=['email', 'otp_type']
        ),
        responses={
            200: openapi.Response(
                description='OTP has been successfully sent to the user\'s email.',
                examples={
                    'application/json': {
                        'success': True,
                        'message': 'An Email has been Sent.'
                    }
                }
            ),
            400: openapi.Response(
                description='Bad request due to missing parameters or user-related issues.',
                examples={
                    'application/json': {
                        'success': False,
                        'message': 'Email is required.'
                    }
                }
            )
        }
    )
    def post(self, request):
        try:
            data = request.data
            email = data.get('email')
            otp_type = data.get('otp_type')

            if users_utils.is_required(email):
                return Response({"success": False, "message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(otp_type):
                return Response({"success": False, "message": "OTP Type is required."}, status=status.HTTP_400_BAD_REQUEST)

            if otp_type == "reset_password":
                if not users_models.User.objects.filter(email=email, is_deleted=False, is_active=False).exists():
                    return Response({"success": False, "message": "User With This Email Not Exist."}, status=status.HTTP_400_BAD_REQUEST)

            if otp_type == "verify_email":
                user = users_models.User.objects.filter(
                    email=email, is_deleted=False, is_active=False).first()
                if user:
                    if user.is_email_verified:
                        return Response({"success": False, "message": "Email is already verified."}, status=status.HTTP_400_BAD_REQUEST)

            users_models.Otp.objects.filter(
                user=email, otp_type=otp_type).delete()

            otp_code = users_models.Otp.objects.create(
                user=email, otp_type=otp_type)

            # send_mail({
            #     "otp_code": otp_code.otp,
            #     "otp_type": otp_code.otp_type,
            #     "email": email,
            #     "subject": "OTP Verification",
            #     "template_name": "email_verification.html",
            # })

            return Response({"success": True, "message": "Please Verify Below OTP code.", "data": otp_code.otp}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    """
    View for verifying OTP sent to a user's registered email address.
    """

    @swagger_auto_schema(
        operation_summary="Verify OTP",
        operation_description="Verify the OTP sent to the user's registered email address.",
        tags=['Auth'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email address'),
                'otp_code': openapi.Schema(type=openapi.TYPE_STRING, description='The OTP code sent to the user'),
                'otp_type': openapi.Schema(type=openapi.TYPE_STRING, description='The type of OTP request (e.g., reset_password, verify_email)')
            },
            required=['email', 'otp_code', 'otp_type']
        ),
        responses={
            200: openapi.Response(
                description='OTP successfully verified.',
                examples={
                    'application/json': {
                        'success': True,
                        # Example for reset_password
                        'message': 'OTP verified successfully. You can now reset your password.'
                    }
                }
            ),
            400: openapi.Response(
                description='Bad request due to missing parameters or invalid OTP.',
                examples={
                    'application/json': {
                        'success': False,
                        'message': 'Email is required.'  # Example for missing email
                    },
                    'application/json': {
                        'success': False,
                        'message': 'OTP has expired. Please request new otp'  # Example for expired OTP
                    },
                    'application/json': {
                        'success': False,
                        'message': 'Invalid OTP.'  # Example for invalid OTP
                    }
                }
            )
        }
    )
    def post(self, request):
        try:
            data = request.data
            email = data.get('email')
            otp_code = data.get('otp_code')
            otp_type = data.get('otp_type')

            if users_utils.is_required(email):
                return Response({"success": False, "message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(otp_code):
                return Response({"success": False, "message": "OTP Code is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(otp_type):
                return Response({"success": False, "message": "OTP Type is required."}, status=status.HTTP_400_BAD_REQUEST)

            otp = users_models.Otp.objects.filter(
                user=email, otp_type=otp_type, otp=otp_code).first()

            if otp:
                if otp.expiry_time < timezone.now():
                    otp.delete()
                    return Response({"success": False, "message": "OTP has expired. Please request new otp"}, status=status.HTTP_400_BAD_REQUEST)

            if otp:
                if otp_type == "reset_password":
                    otp.delete()
                    return Response({"success": True, "message": "OTP verified successfully. You can now reset your password."}, status=status.HTTP_200_OK)
                if otp_type == "verify_email":
                    user = users_models.User.objects.filter(
                        email=email, is_deleted=False, is_active=True).first()
                    otp.delete()
                    if user:
                        user.is_email_verified = True
                        user.save()
                        return Response({"success": True, "message": "Email verified successfully."}, status=status.HTTP_200_OK)
                    else:
                        return Response({"success": False, "message": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

                else:
                    return Response({"success": False, "message": "Invalid OTP Type."}, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({"success": False, "message": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClientView(generics.ListAPIView):

    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = users_serializer.ClientListSerializer

    def get_queryset(self):
        search_params = self.request.query_params.get('search', '')
        user_type = self.request.query_params.get('user_type', 'client')
        is_favorite = self.request.query_params.get('is_favorite', None)

        users = users_models.ClientModel.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-created_at')

        if search_params:
            users = users.filter(Q(client_name__icontains=search_params) | Q(
                email__icontains=search_params)).distinct()

        if user_type:
            users = users.filter(user_type=user_type)

        if is_favorite:
            if is_favorite == 'true':
                users = users.filter(is_favorite=True)
            else:
                users = users.filter(is_favorite=False)

        return users

    @swagger_auto_schema(
        operation_summary="List clients for the authenticated user",
        operation_description="Returns a paginated list of clients associated with the authenticated user.",
        tags=['Client / Supplier'],
        responses={
            200: openapi.Response(
                description="Successful response with paginated list of clients",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of clients'),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description='Next page URL'),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description='Previous page URL'),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            # optionally point to serializer schema
                            items=openapi.Items(type=openapi.TYPE_OBJECT)
                        )
                    }
                )
            ),
            400: openapi.Response(description="Bad request"),
        }
    )
    def get(self, request):
        try:
            queryset = self.get_queryset()

            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(queryset, request)

            serializer = self.serializer_class(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AddClientView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Add a new client",
        operation_description="Allows an authenticated user to add a new client by providing basic details like name, email, and phone number.",
        tags=['Client / Supplier'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['client_name', 'email', 'phone_number'],
            properties={
                'client_name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the client"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Client's email address"),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Client's phone number"),
                'contact_person': openapi.Schema(type=openapi.TYPE_STRING, description="Contact person's name", default=""),
                'shipping_address': openapi.Schema(type=openapi.TYPE_STRING, description="Shipping address", default=""),
                'billing_address': openapi.Schema(type=openapi.TYPE_STRING, description="Billing address", default=""),
                'city': openapi.Schema(type=openapi.TYPE_STRING, description="City", default=""),
                'state': openapi.Schema(type=openapi.TYPE_STRING, description="State", default=""),
                'country': openapi.Schema(type=openapi.TYPE_STRING, description="Country", default=""),
                'zip_code': openapi.Schema(type=openapi.TYPE_STRING, description="Zip/Postal code", default=""),
                'tax_number': openapi.Schema(type=openapi.TYPE_STRING, description="Tax number", default=""),
                'gst_type': openapi.Schema(type=openapi.TYPE_STRING, description="GST type", default=""),
                'pan_number': openapi.Schema(type=openapi.TYPE_STRING, description="PAN number", default=""),
                'payment_term': openapi.Schema(type=openapi.TYPE_STRING, description="Payment terms", default=""),
                'credit_limit': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Credit limit", default=0.0),
                'preferred_payment_method': openapi.Schema(type=openapi.TYPE_STRING, description="Preferred payment method", default=""),
                'bank_details': openapi.Schema(type=openapi.TYPE_STRING, description="Bank details", default=""),
                'notes': openapi.Schema(type=openapi.TYPE_STRING, description="Additional notes", default=""),
                'category': openapi.Schema(type=openapi.TYPE_STRING, description="Client category", default=""),
                'user_type': openapi.Schema(type=openapi.TYPE_STRING, description="User Type Client / Supplier", default=""),
            }
        ),
        responses={
            201: openapi.Response(
                description="Client created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'client_id': openapi.Schema(type=openapi.TYPE_STRING),
                                'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user_fullname': openapi.Schema(type=openapi.TYPE_STRING),
                                'client_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                # You can add other fields here too...
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request",
                examples={
                    "application/json": {
                        "success": False,
                        "message": {
                            "email": ["This field must be unique."]
                        }
                    }
                }
            )
        }
    )
    def post(self, request):
        try:
            data = request.data
            user = request.user
            client_name = data.get('client_name')
            email = data.get('email')
            phone_number = data.get('phone_number')

            if users_utils.is_required(client_name):
                return Response({"success": False, "message": "Client Name is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(email):
                return Response({"success": False, "message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(phone_number):
                return Response({"success": False, "message": "Phone Number is required."}, status=status.HTTP_400_BAD_REQUEST)

            data['user'] = user.user_id
            serializer = users_serializer.ClientSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "Client added successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)

            else:
                return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_201_CREATED)


class ClientDetailView(APIView):

    permission_classes = [IsAuthenticated]
    serializer_class = users_serializer.ClientSerializer

    @swagger_auto_schema(
        operation_summary="Retrieve a client by ID",
        operation_description="Returns a client's details by client ID for the authenticated user.",
        tags=['Client / Supplier'],
        manual_parameters=[
            openapi.Parameter(
                'client_id',
                openapi.IN_PATH,
                description="UUID of the client",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Client found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "client_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "client_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "email": openapi.Schema(type=openapi.TYPE_STRING),
                                "phone_number": openapi.Schema(type=openapi.TYPE_STRING),
                                "user_fullname": openapi.Schema(type=openapi.TYPE_STRING),
                                "created_at": openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                "updated_at": openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                # Add more fields from ClientSerializer if needed
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request (e.g., missing client ID)",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Client ID is required."
                    }
                }
            ),
            404: openapi.Response(
                description="Client not found",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Client not found."
                    }
                }
            ),
        }
    )
    def get(self, request, client_id):
        try:
            user = request.user

            if users_utils.is_required(client_id):
                return Response({"success": False, "message": "Client ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                client = users_models.ClientModel.objects.get(
                    client_id=client_id,
                    user=user,
                    is_deleted=False,
                )

                data = {
                    "client_id": client.client_id,
                    "client_name": client.client_name,
                    "email": client.email,
                    "phone_number": client.phone_number,
                    "client_since": client.created_at.strftime("%b %d,%Y")
                }

                try:
                    invoices = products_models.Invoice.objects.filter(
                        user=user, client=client, is_deleted=False)
                    total_invoiced = invoices.aggregate(
                        total=Sum('total')).get('total') or Decimal('0.00')

                    paid_invoices = invoices.filter(status__iexact='Paid')
                    total_paid = paid_invoices.aggregate(
                        total=Sum('total')).get('total') or Decimal('0.00')

                    outstanding = Decimal(total_invoiced) - Decimal(total_paid)

                    last_paid_invoice = paid_invoices.order_by(
                        '-updated_at').first()
                    if last_paid_invoice and last_paid_invoice.updated_at:
                        delta = timezone.now() - last_paid_invoice.updated_at
                        days = delta.days
                        if days <= 0:
                            last_payment_text = "Last payment: today"
                        elif days == 1:
                            last_payment_text = "Last payment: 1 day ago"
                        else:
                            last_payment_text = f"Last payment: {days} days ago"
                    else:
                        last_payment_text = "No payments yet"

                    now = timezone.now()
                    start_of_month = now.replace(
                        day=1, hour=0, minute=0, second=0, microsecond=0)
                    paid_this_month = paid_invoices.filter(updated_at__gte=start_of_month).aggregate(
                        total=Sum('total')).get('total') or Decimal('0.00')

                    recent_invoices = []
                    try:
                        recent_qs = invoices.order_by('-issue_date')[:5]
                        for inv in recent_qs:
                            if inv.payment_due:
                                due_text = f"Due {inv.payment_due.strftime('%b %d, %Y')}"
                            else:
                                due_text = ""

                            total_val = inv.total if inv.total is not None else Decimal(
                                '0.00')
                            try:
                                total_str = f"${Decimal(total_val):,.2f}"
                            except Exception:
                                total_str = f"${total_val}"

                            recent_invoices.append({
                                "invoice_number": inv.invoice_number or str(inv.invoice_id),
                                "due_date": due_text,
                                "total": total_str,
                                "status": inv.status or "",
                            })
                    except Exception:
                        recent_invoices = []

                    data.update({
                        "outstanding_balance": f"{Decimal(outstanding):.2f}",
                        "total_paid": f"{Decimal(total_paid):.2f}",
                        "paid_this_month": f"{Decimal(paid_this_month):.2f}",
                        "last_payment": last_payment_text,
                        "recent_invoices": recent_invoices,
                        # "invoices": products_serializer.InvoiceSerializer(invoices, many=True).data,
                    })
                except Exception:
                    data.update({
                        "outstanding_balance": "0.00",
                        "total_paid": "0.00",
                        "paid_this_month": "0.00",
                        "last_payment": "No payments yet",
                        "invoices": []
                    })

                return Response({"success": True, "message": "Client Details fetched", "data": data}, status=status.HTTP_200_OK)

            except users_models.ClientModel.DoesNotExist:
                return Response({"success": False, "message": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update a client",
        operation_description="Updates details of a specific client by its ID. Accepts partial data.",
        tags=['Client / Supplier'],
        manual_parameters=[
            openapi.Parameter(
                'client_id',
                openapi.IN_PATH,
                description="UUID of the client to be updated",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'client_name': openapi.Schema(type=openapi.TYPE_STRING, description="Updated client name"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'contact_person': openapi.Schema(type=openapi.TYPE_STRING),
                'shipping_address': openapi.Schema(type=openapi.TYPE_STRING),
                'billing_address': openapi.Schema(type=openapi.TYPE_STRING),
                'city': openapi.Schema(type=openapi.TYPE_STRING),
                'state': openapi.Schema(type=openapi.TYPE_STRING),
                'country': openapi.Schema(type=openapi.TYPE_STRING),
                'zip_code': openapi.Schema(type=openapi.TYPE_STRING),
                'tax_number': openapi.Schema(type=openapi.TYPE_STRING),
                'gst_type': openapi.Schema(type=openapi.TYPE_STRING),
                'pan_number': openapi.Schema(type=openapi.TYPE_STRING),
                'payment_term': openapi.Schema(type=openapi.TYPE_STRING),
                'credit_limit': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                'preferred_payment_method': openapi.Schema(type=openapi.TYPE_STRING),
                'bank_details': openapi.Schema(type=openapi.TYPE_STRING),
                'notes': openapi.Schema(type=openapi.TYPE_STRING),
                'category': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: openapi.Response(
                description="Client updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'client_id': openapi.Schema(type=openapi.TYPE_STRING),
                                'client_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                                'updated_at': openapi.Schema(type=openapi.TYPE_STRING),
                                # Add additional fields as needed
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Validation failed",
                examples={
                    "application/json": {
                        "success": False,
                        "error": {
                            "email": ["This field must be unique."]
                        }
                    }
                }
            ),
            404: openapi.Response(
                description="Client not found",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Client not found."
                    }
                }
            )
        }
    )
    def put(self, request, client_id):
        try:
            user = request.user
            data = request.data

            if users_utils.is_required(client_id):
                return Response({"success": False, "message": "Client ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                client_instance = users_models.ClientModel.objects.get(
                    client_id=client_id, user=user, is_deleted=False)
            except users_models.ClientModel.DoesNotExist:
                return Response({"success": False, "message": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = self.serializer_class(
                instance=client_instance, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "Client updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

            return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete a client",
        operation_description="Deletes a client (soft delete) by its ID for the authenticated user.",
        tags=['Client / Supplier'],
        manual_parameters=[
            openapi.Parameter(
                'client_id',
                openapi.IN_PATH,
                description="UUID of the client to delete",
                type=openapi.TYPE_STRING,
                required=True,
                format=openapi.FORMAT_UUID
            )
        ],
        responses={
            200: openapi.Response(
                description="Client deleted successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Client deleted successfully."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request or missing client ID",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Client ID is required."
                    }
                }
            ),
            404: openapi.Response(
                description="Client not found",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Client not found."
                    }
                }
            ),
        }
    )
    def delete(self, request, client_id):
        try:
            user = request.user

            if users_utils.is_required(client_id):
                return Response({"success": False, "message": "Client ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            if not users_models.ClientModel.objects.filter(client_id=client_id, user=user, is_deleted=False).exists():
                return Response({"success": False, "message": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

            client = users_models.ClientModel.objects.get(
                client_id=client_id, user=user, is_deleted=False)
            client.delete()
            return Response({"success": True, "message": "Client deleted successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AddRemoveFavoriteClient(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Add or Remove a client from favorites",
        operation_description="Add or remove a client from the authenticated user's favorite clients list.",
        tags=['Client / Supplier'],
        manual_parameters=[
            openapi.Parameter(
                'is_favorite', openapi.IN_QUERY,
                description="Set the client's favorite status (true/false).",
                type=openapi.TYPE_STRING,
                enum=['true', 'false'],
                default='false'
            ),
            openapi.Parameter(
                'client_id', openapi.IN_PATH,
                description="The client ID to update the favorite status for.",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Favorite status updated successfully.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Favorite status updated successfully.",
                        "data": {
                            "client_id": 123,
                            "is_favorite": True
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request, missing parameters or invalid input.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Client ID is required."
                    }
                }
            ),
            404: openapi.Response(
                description="Client not found.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Client not found."
                    }
                }
            )
        }
    )
    def get(self, request, client_id):
        try:
            user = request.user
            is_favorite = request.query_params.get('is_favorite', 'false')

            if users_utils.is_required(client_id):
                return Response({"success": False, "message": "Client ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(is_favorite):
                return Response({"success": False, "message": "is_favorite parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

            client_obj = users_models.ClientModel.objects.filter(
                client_id=client_id, user=user, is_deleted=False).first()

            if not client_obj:
                return Response({"success": False, "message": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

            if is_favorite.lower() == 'true':
                client_obj.is_favorite = True
            else:
                client_obj.is_favorite = False

            client_obj.save()
            return Response({"success": True, "message": "Favorite status updated successfully.", "data": {"client_id": client_obj.client_id, "is_favorite": client_obj.is_favorite}}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserLoginHistory(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = users_serializer.UserLoginSerializer
    pagination_class = CustomPagination

    def get_queryset(self):

        login_history_obj = users_models.UserLogin.objects.filter(
            user=self.request.user).order_by('-created_at')

        serializer = self.serializer_class(login_history_obj, many=True)

        return serializer.data

    @swagger_auto_schema(
        operation_summary="Retrieve User Login History",
        operation_description="Fetches a paginated list of the authenticated user's login history records.",
        tags=['User'],
        manual_parameters=[
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number for pagination.",
                type=openapi.TYPE_INTEGER,
                required=False,
                example=1
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of results to return per page.",
                type=openapi.TYPE_INTEGER,
                required=False,
                example=10
            )
        ],
        responses={
            200: openapi.Response(
                description="Login history retrieved successfully.",
                examples={
                    "application/json": {
                        "count": 25,
                        "next": "https://api.example.com/api/user/login-history/?page=2",
                        "previous": None,
                        "results": [
                            {
                                "id": 12,
                                "user": 5,
                                "ip_address": "192.168.1.45",
                                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                                "login_time": "2025-10-27T09:45:32Z",
                                "created_at": "2025-10-27T09:45:32Z"
                            }
                        ]
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request — an error occurred while fetching login history.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "An error occurred while fetching login history."
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized — user must be authenticated.",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
        }
    )
    def get(self, request):
        try:
            queryset = self.get_queryset()

            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(queryset, request)
            return paginator.get_paginated_response(result_page)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserCompany(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = users_serializer.UserCompanySerializer

    @swagger_auto_schema(
        operation_summary="Retrieve Authenticated User's Company Details",
        operation_description="Fetches the company details associated with the authenticated user.",
        tags=['Company'],
        responses={
            200: openapi.Response(
                description="Company details fetched successfully.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Company details fetched successfully.",
                        "data": {
                            "id": 15,
                            "name": "TechCorp Solutions",
                            "registration_number": "TC1234567",
                            "email": "info@techcorp.com",
                            "phone": "+1-555-1234",
                            "address": "123 Silicon Valley Blvd, CA, USA",
                            "created_at": "2025-01-15T09:45:32Z",
                            "updated_at": "2025-09-10T12:22:18Z"
                        }
                    }
                }
            ),
            404: openapi.Response(
                description="Company not found for the authenticated user.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "User does not have a company associated with it."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request — an unexpected error occurred.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "An unexpected error occurred."
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized — user must be authenticated.",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
        }
    )
    def get(self, request):
        try:
            user = request.user

            if not users_models.UserCompany.objects.filter(user=user, is_deleted=False).exists():
                return Response({"success": False, "message": "User does not have a company associated with it."}, status=status.HTTP_404_NOT_FOUND)

            company_obj = users_models.UserCompany.objects.get(
                user=user, is_deleted=False)
            serializer = self.serializer_class(company_obj).data
            return Response({"success": True, "message": "Company details fetched successfully.", "data": serializer}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Add a Company for the Authenticated User",
        operation_description=(
            "Creates and associates a new company with the authenticated user. "
            "A user can only have one active company record."
        ),
        tags=['Company'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                'company_name',
                'registration_number',
                'tax_id',
                'business_type',
                'founded_date',
                'industry',
                'address',
                'country_code',
                'phone_number',
                'company_email'
            ],
            properties={
                'company_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Name of the company.",
                    example="Dummy"
                ),
                'registration_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Official registration or incorporation number.",
                    example="12345678"
                ),
                'tax_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Tax identification number for the company.",
                    example="123"
                ),
                'business_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Type of business or sector.",
                    example="Manufacturing"
                ),
                'founded_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='date',
                    description="Date when the company was founded (YYYY-MM-DD).",
                    example="2024-05-12"
                ),
                'industry': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Industry the company operates in.",
                    example="Automotive"
                ),
                'address': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Registered or main address of the company.",
                    example="123 Industrial Area, Mumbai, India"
                ),
                'country_code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Country calling code (e.g., +91, +1).",
                    example="+91"
                ),
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Primary company phone number.",
                    example="123456789"
                ),
                'company_email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='email',
                    description="Official email address of the company.",
                    example="dummy@gmail.com"
                ),
                'website': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='uri',
                    description="Official website URL of the company.",
                    example="https://dummy.com"
                ),
                'bank_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Name of the bank where the company holds an account.",
                    example="ICICI"
                ),
                'account_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Company’s bank account number.",
                    example="123455"
                ),
                'routing_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Bank routing number or IFSC code.",
                    example="Asd213234"
                ),
            }
        ),
        responses={
            201: openapi.Response(
                description="Company added successfully.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Company added successfully.",
                        "data": {
                            "id": 15,
                            "company_name": "Dummy",
                            "registration_number": "12345678",
                            "tax_id": "123",
                            "business_type": "Manufacturing",
                            "founded_date": "2024-05-12",
                            "industry": "Automotive",
                            "address": "123 Industrial Area, Mumbai, India",
                            "country_code": "+91",
                            "phone_number": "123456789",
                            "company_email": "dummy@gmail.com",
                            "website": "https://dummy.com",
                            "bank_name": "ICICI",
                            "account_number": "123455",
                            "routing_number": "Asd213234",
                            "user": 7,
                            "created_at": "2025-10-27T09:45:32Z"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request — missing or invalid input.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Company Name is required."
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized — authentication required.",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
        }
    )
    def post(self, request):
        try:
            user = request.user
            data = request.data
            company_name = data.get('company_name')

            if users_utils.is_required(company_name):
                return Response({"success": False, "message": "Company Name is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_models.UserCompany.objects.filter(user=user, is_deleted=False).exists():
                return Response({"success": False, "message": "User already has a company associated with it."}, status=status.HTTP_400_BAD_REQUEST)

            data['user'] = user.user_id
            serializer = self.serializer_class(data=data)

            if serializer.is_valid():
                serializer.save(user=user)
                return Response({"success": True, "message": "Company added successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Update Authenticated User's Company Details",
        operation_description=(
            "Updates the details of the company associated with the authenticated user. "
            "All fields are optional; only provided fields will be updated."
        ),
        tags=['Company'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'company_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Name of the company.",
                    example="Dummy Updated"
                ),
                'registration_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Official registration or incorporation number.",
                    example="12345678"
                ),
                'tax_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Tax identification number for the company.",
                    example="123"
                ),
                'business_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Type of business or sector.",
                    example="Manufacturing"
                ),
                'founded_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='date',
                    description="Date when the company was founded (YYYY-MM-DD).",
                    example="2024-05-12"
                ),
                'industry': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Industry the company operates in.",
                    example="Automotive"
                ),
                'address': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Registered or main address of the company.",
                    example="123 Industrial Area, Mumbai, India"
                ),
                'country_code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Country calling code (e.g., +91, +1).",
                    example="+91"
                ),
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Primary company phone number.",
                    example="123456789"
                ),
                'company_email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='email',
                    description="Official email address of the company.",
                    example="dummy@gmail.com"
                ),
                'website': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='uri',
                    description="Official website URL of the company.",
                    example="https://dummy.com"
                ),
                'bank_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Name of the bank where the company holds an account.",
                    example="ICICI"
                ),
                'account_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Company’s bank account number.",
                    example="123455"
                ),
                'routing_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Bank routing number or IFSC code.",
                    example="Asd213234"
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Company updated successfully.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Company updated successfully.",
                        "data": {
                            "id": 15,
                            "company_name": "Dummy Updated",
                            "registration_number": "12345678",
                            "tax_id": "123",
                            "business_type": "Manufacturing",
                            "founded_date": "2024-05-12",
                            "industry": "Automotive",
                            "address": "123 Industrial Area, Mumbai, India",
                            "country_code": "+91",
                            "phone_number": "9876543210",
                            "company_email": "updated@dummy.com",
                            "website": "https://dummy.com",
                            "bank_name": "ICICI",
                            "account_number": "123455",
                            "routing_number": "Asd213234",
                            "updated_at": "2025-10-27T11:15:32Z"
                        }
                    }
                }
            ),
            404: openapi.Response(
                description="No company associated with the user.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "User does not have a company associated with it."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request — invalid or missing data.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Invalid data provided."
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized — authentication required.",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
        }
    )
    def put(self, request):
        try:
            user = request.user
            data = request.data

            company_obj = users_models.UserCompany.objects.filter(
                user=user, is_deleted=False).first()

            if not company_obj:
                return Response({"success": False, "message": "User does not have a company associated with it."}, status=status.HTTP_404_NOT_FOUND)

            serializer = self.serializer_class(
                instance=company_obj, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "Company updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

            return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete Authenticated User's Company",
        operation_description=(
            "Deletes the company associated with the authenticated user. "
            "If no active company is found, a 404 error is returned."
        ),
        tags=['Company'],
        responses={
            200: openapi.Response(
                description="Company deleted successfully.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Company deleted successfully."
                    }
                }
            ),
            404: openapi.Response(
                description="No active company found for the user.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "User does not have a company associated with it."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request — an unexpected error occurred.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "An unexpected error occurred."
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized — authentication required.",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
        }
    )
    def delete(self, request):
        try:
            user = request.user

            company_obj = users_models.UserCompany.objects.filter(
                user=user, is_deleted=False).first()

            if not company_obj:
                return Response({"success": False, "message": "User does not have a company associated with it."}, status=status.HTTP_404_NOT_FOUND)

            company_obj.delete()

            return Response({"success": True, "message": "Company deleted successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceListByClientID(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = products_serializer.InvoiceSerializer

    def get_queryset(self, client_id):

        invoices = products_models.Invoice.objects.filter(
            user=self.request.user, client=client_id, is_deleted=False)

        return invoices

    @swagger_auto_schema(
        operation_summary="Retrieve Invoices by Client ID",
        operation_description="Fetches a paginated list of invoices associated with a specific client ID for the authenticated user.",
        tags=['Client / Supplier'],
        manual_parameters=[
            openapi.Parameter(
                'client_id',
                openapi.IN_PATH,
                description="UUID of the client to fetch invoices for",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def get(self, request, client_id):
        try:
            queryset = self.get_queryset(client_id)

            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(queryset, request)

            serializer = self.serializer_class(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetInfoFromGSTNumber(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Company Info from GST Number",
        operation_description="Retrieves company information based on the provided GST number.",
        tags=['Company'],
        manual_parameters=[
            openapi.Parameter(
                'gst_number', openapi.IN_QUERY,
                description="GST number to fetch company information for.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def get(self, request):
        try:
            gst_number = request.query_params.get('gst_number')

            if users_utils.is_required(gst_number):
                return Response({"success": False, "message": "GST number is required."}, status=status.HTTP_400_BAD_REQUEST)

            company_info = users_utils.fetch_company_info_from_gst_number(
                gst_number)

            if not company_info.get('data'):
                return Response({"success": False, "message": "No company found for the provided GST number."}, status=status.HTTP_404_NOT_FOUND)

            return Response({"success": True, "message": "Company details fetched successfully.", "data": company_info.get('data')}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserExpenseList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = users_serializer.UserExpenseSerializer

    def get_queryset(self):

        expenses = users_models.UserExpense.objects.filter(
            user=self.request.user).order_by('-created_at')

        return expenses

    def get(self, request):
        try:
            queryset = self.get_queryset()

            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(queryset, request)

            serializer = self.serializer_class(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AddUserExpense(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = users_serializer.UserExpenseSerializer

    def post(self, request):
        try:
            user = request.user
            data = request.data
            expense_name = data.get('expense_name')
            amount = data.get('amount')
            category = data.get('category')
            expense_date = data.get('expense_date')

            if users_utils.is_required(expense_name):
                return Response({"success": False, "message": "Expense name is required."}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(amount):
                return Response({"success": False, "message": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(category):
                return Response({"success": False, "message": "Category is required"}, status=status.HTTP_400_BAD_REQUEST)

            if users_utils.is_required(expense_date):
                return Response({"success": False, "message": "Expense Date is required"}, status=status.HTTP_400_BAD_REQUEST)

            data['user'] = user.user_id
            serializer = self.serializer_class(data=data)

            if serializer.is_valid():
                expense_data = serializer.save()

                return Response({"success": True, "message": "Expense Added", "data": self.serializer_class(expense_data).data}, status=status.HTTP_200_OK)

            return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExpenseReportPage(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            search = request.query_params.get('search', '')
            time = request.query_params.get('time', '')

            expenses = users_models.UserExpense.objects.filter(
                user=user).order_by('-created_at')

            if search:
                expenses = expenses.filter(
                    Q(expense_name__icontains=search) |
                    Q(category__icontains=search) |
                    Q(description__icontains=search)
                )

            # prepare date ranges
            today = timezone.localdate()
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)

            if time:
                if time == 'this_week':
                    # 'this_week' is defined as the last 7 days excluding today and yesterday
                    expenses = expenses.filter(
                        expense_date__gte=week_ago, expense_date__lt=yesterday)

                elif time == 'this_month':
                    expenses = expenses.filter(
                        expense_date__year=today.year, expense_date__month=today.month)

                elif time == 'last_month':
                    # Robustly calculate the date range for the previous month
                    first_day_current_month = today.replace(day=1)
                    last_day_last_month = first_day_current_month - \
                        timedelta(days=1)
                    first_day_last_month = last_day_last_month.replace(day=1)
                    expenses = expenses.filter(
                        expense_date__gte=first_day_last_month, expense_date__lte=last_day_last_month)

            # Querysets for each range (exclude overlaps)
            today_qs = expenses.filter(expense_date=today)
            yesterday_qs = expenses.filter(expense_date=yesterday)
            # this_week: last 7 days excluding today and yesterday
            this_week_qs = expenses.filter(
                expense_date__gte=week_ago, expense_date__lt=yesterday)

            # Serialize results
            today_ser = users_serializer.UserExpenseSerializer(
                today_qs, many=True).data
            yesterday_ser = users_serializer.UserExpenseSerializer(
                yesterday_qs, many=True).data
            this_week_ser = users_serializer.UserExpenseSerializer(
                this_week_qs, many=True).data

            # compute totals for each group
            today_total = today_qs.aggregate(total=Sum('amount'))[
                'total'] or Decimal('0.00')
            yesterday_total = yesterday_qs.aggregate(total=Sum('amount'))[
                'total'] or Decimal('0.00')
            this_week_total = this_week_qs.aggregate(total=Sum('amount'))[
                'total'] or Decimal('0.00')

            recent_expenses = {
                "today": {"items": today_ser, "total": int(today_total)},
                "yesterday": {"items": yesterday_ser, "total": int(yesterday_total)},
                "this_week": {"items": this_week_ser, "total": int(this_week_total)},
            }

            # Allow empty 'time' for all-time report, but validate if provided
            if time and time not in ['this_week', 'this_month', 'last_month']:
                return Response({"success": False, "message": "Invalid time parameter. Use 'this_week', 'this_month', or 'last_month'."}, status=status.HTTP_400_BAD_REQUEST)

            # Use the 'expenses' queryset which may have search filters applied
            expense_pr = expenses

            # Calculate expense percentages by category
            total_expense_amount = expense_pr.aggregate(
                total=Sum('amount'))['total'] or Decimal('0.00')
            expense_categories = [
                "Food & Dining",
                "Transport",
                "Shopping",
                "Bills",
                "Entertainment"
            ]
            category_percentages = []

            if total_expense_amount > Decimal('0.00'):
                # Group by category and sum amounts from the correctly filtered queryset
                category_totals = expense_pr.values(
                    'category').annotate(total=Sum('amount'))

                # Create a dictionary for quick lookup
                totals_map = {item['category']: item['total']
                              for item in category_totals}

                main_categories_spent = Decimal('0.00')
                for category in expense_categories:
                    amount_spent = totals_map.get(category, Decimal('0.00'))
                    percentage = (amount_spent / total_expense_amount) * 100
                    category_percentages.append({
                        'category': category,
                        'percentage': round(percentage, 2)
                    })
                    main_categories_spent += amount_spent

                # Calculate "Other" category for expenses not in the main list
                other_spent = total_expense_amount - main_categories_spent
                if other_spent > Decimal('0.00'):
                    percentage = (other_spent / total_expense_amount) * 100
                    category_percentages.append({
                        'category': 'Other',
                        'percentage': round(percentage, 2)
                    })

            # Compute last calendar month's date range
            first_day_current_month = today.replace(day=1)
            last_day_last_month = first_day_current_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)

            # Build queryset for last month and apply same search filters
            last_month_qs = users_models.UserExpense.objects.filter(
                user=user,
                expense_date__gte=first_day_last_month,
                expense_date__lte=last_day_last_month,
            )

            if search:
                last_month_qs = last_month_qs.filter(
                    Q(expense_name__icontains=search) |
                    Q(category__icontains=search) |
                    Q(description__icontains=search)
                )

            last_month_total = last_month_qs.aggregate(total=Sum('amount'))[
                'total'] or Decimal('0.00')

            # total_expense_amount is the total for the current filtered period (could be this_month, this_week, last_month, or all-time)
            current_total = total_expense_amount

            # Calculate percentage change vs last month. If last month total is zero, set percentage_change to None
            if last_month_total > Decimal('0.00'):
                percentage_change = round(
                    ((current_total - last_month_total) / last_month_total) * 100, 2)
            else:
                percentage_change = 0

            year = today.year
            month = today.month
            days_in_month = calendar.monthrange(year, month)[1]
            first_of_month = today.replace(day=1)

            # Build a map of expense_date -> total for the month
            month_qs = expense_pr.filter(expense_date__year=year, expense_date__month=month)
            month_totals = month_qs.values('expense_date').annotate(total=Sum('amount'))
            month_totals_map = {item['expense_date']: item['total'] for item in month_totals}

            labels = []
            data = []
            for d in range(1, days_in_month + 1):
                day_date = first_of_month + timedelta(days=(d - 1))
                labels.append(day_date.isoformat())
                amt = month_totals_map.get(day_date, Decimal('0.00'))
                # convert Decimal to float for charting (round to 2 decimals)
                data.append(float(round(amt, 2)))

            chart_data = {
                'labels': labels,
                'data': data,
                'total_for_month': float(round(sum(data), 2))
            }

            response_data = {
                "recent_expenses": recent_expenses,
                "category_percentages": category_percentages,
                "total_spent": float(round((users_models.UserExpense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')), 2)),
                "chart_data": chart_data,
                "compare_to_last_month": {
                    "last_month_total": int(last_month_total),
                    "percentage_change": percentage_change,
                }
            }

            return Response({"success": True, "message": "Recent expenses fetched successfully.", "data": response_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StatisticsPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            invoices = products_models.Invoice.objects.filter(
                user=user, invoice_type="sales")

            if start_date:
                invoices = invoices.filter(issue_date__gte=start_date)
            if end_date:
                invoices = invoices.filter(issue_date__lte=end_date)

            paid_invoices = invoices.filter(status="Paid")

            total_revenue = paid_invoices.aggregate(
                total=Sum('total'))['total'] or Decimal('0.00')

            pending_amount = invoices.filter(status="Pending").aggregate(
                total=Sum('total'))['total'] or Decimal('0.00')

            expenses = users_models.UserExpense.objects.filter(user=user)
            if start_date:
                expenses = expenses.filter(expense_date__gte=start_date)
            if end_date:
                expenses = expenses.filter(expense_date__lte=end_date)

            total_expense = expenses.aggregate(
                total=Sum('amount'))['total'] or Decimal('0.00')

            # COGS
            cogs = products_models.InvoiceItems.objects.filter(
                invoice__in=paid_invoices
            ).aggregate(
                total_cogs=Sum(F('qty') * F('product__cost_price'))
            )['total_cogs'] or Decimal('0.00')

            gross_profit = total_revenue - cogs
            operating_expense = total_expense
            ebitda = gross_profit - operating_expense
            net_profit = ebitda

            # Cash Flow
            purchases = products_models.Invoice.objects.filter(
                user=user, invoice_type="purchase", status="Paid"
            )

            if start_date:
                purchases = purchases.filter(issue_date__gte=start_date)
            if end_date:
                purchases = purchases.filter(issue_date__lte=end_date)

            paid_purchases = purchases.aggregate(total=Sum('total'))[
                'total'] or Decimal('0.00')

            cash_flow = total_revenue - (total_expense + paid_purchases)

            # ROI
            total_investment = cogs + total_expense
            if total_investment > Decimal('0.00'):
                roi = (net_profit / total_investment) * 100
            else:
                roi = Decimal('0.00')

            data = {
                "total_revenue": total_revenue,
                "total_expense": total_expense,
                "net_profit": net_profit,
                "pending_amount": pending_amount,
                "gross_profit": gross_profit,
                "operating_expense": operating_expense,
                "ebitda": ebitda,
                "cash_flow": cash_flow,
                "roi": round(roi, 2),
            }

            return Response({"success": True, "message": "Statistics page data fetched successfully.", "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SalesByClientReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            invoices = products_models.Invoice.objects.filter(
                user=user, invoice_type="sales", is_deleted=False)

            if start_date:
                invoices = invoices.filter(issue_date__gte=start_date)
            if end_date:
                invoices = invoices.filter(issue_date__lte=end_date)

            total_revenue = invoices.filter(status="Paid").aggregate(
                total=Sum('total'))['total'] or Decimal('0.00')

            clients_sales = invoices.values(
                'client__client_id', 'client__client_name', 'client__email', 'client__phone_number'
            ).annotate(
                total_sales=Sum('total'),
                paid_amount=Sum('total', filter=Q(status="Paid")),
                order_count=Count('invoice_id')
            ).order_by('-total_sales')

            top_clients = []
            for item in clients_sales:
                if item['client__client_id']:
                    total_sales = item['total_sales'] or Decimal('0.00')
                    paid_amount = item['paid_amount'] or Decimal('0.00')
                    top_clients.append({
                        "client_id": item['client__client_id'],
                        "client_name": item['client__client_name'],
                        "email": item['client__email'],
                        "phone_number": item['client__phone_number'],
                        "total_sales": total_sales,
                        "paid_amount": paid_amount,
                        "outstanding_amount": total_sales - paid_amount,
                        "order_count": item['order_count']
                    })

            def _parse_date(s):
                try:
                    return datetime.fromisoformat(s).date()
                except Exception:
                    try:
                        return datetime.strptime(s.split('T')[0], '%Y-%m-%d').date()
                    except Exception:
                        return None

            start_dt = _parse_date(start_date) if start_date else None
            end_dt = _parse_date(end_date) if end_date else None

            today = datetime.now().date()
            if not end_dt:
                end_dt = today

            def add_months(src_date, months):
                year = src_date.year + (src_date.month - 1 + months) // 12
                month = (src_date.month - 1 + months) % 12 + 1
                return datetime(year, month, 1).date()

            end_month = datetime(end_dt.year, end_dt.month, 1).date()
            if start_dt:
                start_month = datetime(start_dt.year, start_dt.month, 1).date()
            else:
                start_month = add_months(end_month, -11)

            monthly_qs = invoices.filter(
                issue_date__gte=start_month,
                issue_date__lte=end_dt,
                status="Paid"
            ).annotate(month=TruncMonth('issue_date')).values('month').annotate(revenue=Sum('total')).order_by('month')

            revenue_map = {}
            for m in monthly_qs:
                key = m.get('month')
                if hasattr(key, 'date'):
                    key = key.date()
                revenue_map[key] = m.get('revenue') or Decimal('0.00')

            labels = []
            revenue_data = []
            cur = start_month
            while cur <= end_month:
                labels.append(cur.strftime('%b'))
                val = revenue_map.get(cur, Decimal('0.00'))
                revenue_data.append(float(val))
                cur = add_months(cur, 1)

            data = {
                "total_revenue": total_revenue,
                "top_clients": top_clients,
                "monthly_chart": {
                    "labels": labels,
                    "revenue": revenue_data
                }
            }

            return Response({"success": True, "message": "Sales by client report fetched successfully.", "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SalesByProductView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            search = request.query_params.get('search')
            time_frame = request.query_params.get('time_frame')

            filters = Q(
                invoice__user=user,
                invoice__invoice_type="sales",
                invoice__is_deleted=False,
                product__is_deleted=False
            )

            if time_frame:
                if time_frame not in ['this_week', 'this_month', 'last_month']:
                    return Response({"success": False, "message": "Invalid time_frame parameter. Use 'this_week', 'this_month', or 'last_month'."}, status=status.HTTP_400_BAD_REQUEST)

                today = timezone.localdate()
                if time_frame == 'this_week':
                    week_ago = today - timedelta(days=7)
                    filters &= Q(invoice__issue_date__gte=week_ago,
                                 invoice__issue_date__lt=today)
                elif time_frame == 'this_month':
                    filters &= Q(invoice__issue_date__year=today.year,
                                 invoice__issue_date__month=today.month)
                elif time_frame == 'last_month':
                    first_day_current_month = today.replace(day=1)
                    last_day_last_month = first_day_current_month - \
                        timedelta(days=1)
                    first_day_last_month = last_day_last_month.replace(day=1)
                    filters &= Q(invoice__issue_date__gte=first_day_last_month,
                                 invoice__issue_date__lte=last_day_last_month)

            elif start_date or end_date:
                if start_date:
                    filters &= Q(invoice__issue_date__gte=start_date)
                if end_date:
                    filters &= Q(invoice__issue_date__lte=end_date)

            if search:
                filters &= Q(product__name__icontains=search)

            sales_data = products_models.InvoiceItems.objects.filter(filters).values(
                'product__product_id',
                'product__name',
                'product__category__category_name'
            ).annotate(
                total_quantity_sold=Sum('qty'),
                total_revenue=Sum(F('qty') * F('price'))
            ).order_by('-total_revenue')

            product_sales = []
            for item in sales_data:
                product_sales.append({
                    "product_id": item['product__product_id'],
                    "product_name": item['product__name'],
                    "category": item['product__category__category_name'],
                    "total_quantity_sold": item['total_quantity_sold'] or 0,
                    "total_revenue": item['total_revenue'] or Decimal('0.00'),
                })

            return Response({"success": True, "message": "Sales by product report fetched successfully.", "data": product_sales}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SalesByDateRange(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            search = request.query_params.get('search')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            customer = request.query_params.get('customer')
            product = request.query_params.get('product')

            filters = Q(
                invoice__user=user,
                invoice__invoice_type="sales",
                invoice__is_deleted=False,
                product__is_deleted=False
            )

            if start_date or end_date:
                if start_date:
                    filters &= Q(invoice__issue_date__gte=start_date)
                if end_date:
                    filters &= Q(invoice__issue_date__lte=end_date)

            if search:
                filters &= Q(product__name__icontains=search)

            if customer:
                filters &= Q(invoice__client__client_id=customer)

            if product:
                filters &= Q(product__product_id=product)

            sales_data = products_models.InvoiceItems.objects.filter(filters).aggregate(
                total_quantity_sold=Sum('qty'),
                total_sales=Sum(F('qty') * F('price')),
                total_tax=Sum('tax'),
                total_discount=Sum('discount_amount')
            )

            total_sales = sales_data.get('total_sales') or Decimal('0.00')
            total_tax = sales_data.get('total_tax') or Decimal('0.00')
            total_discount = sales_data.get(
                'total_discount') or Decimal('0.00')
            total_quantity_sold = sales_data.get('total_quantity_sold') or 0

            net_sales = total_sales - total_discount

            invoice_items = products_models.InvoiceItems.objects.filter(filters).select_related(
                'invoice', 'invoice__client', 'product'
            ).order_by('-invoice__issue_date')

            details = []
            for item in invoice_items:
                details.append({
                    "invoice_number": item.invoice.invoice_number,
                    "date": item.invoice.issue_date,
                    "customer_name": item.invoice.client.client_name if item.invoice.client else "",
                    "item_name": item.product.name if item.product else "",
                    "quantity": item.qty,
                    "price": item.price,
                    "total": (item.qty * item.price) if item.qty and item.price else 0
                })

            data = {
                "total_sales": total_sales,
                "total_tax": total_tax,
                "total_discount": total_discount,
                "net_sales": net_sales,
                "total_quantity_sold": total_quantity_sold,
                "details": details
            }

            return Response({"success": True, "message": "Sales by date range fetched successfully.", "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SalesSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            time_frame = request.query_params.get('time_frame')

            sales_data = products_models.InvoiceItems.objects.filter(
                invoice__user=user,
                invoice__invoice_type="sales",
                invoice__is_deleted=False,
                product__is_deleted=False
            )

            invoices = products_models.Invoice.objects.filter(
                user=user,
                invoice_type="sales",
                is_deleted=False
            )

            if time_frame:
                today = timezone.localdate()
                if time_frame == 'this_week':
                    week_ago = today - timedelta(days=7)
                    sales_data = sales_data.filter(
                        invoice__issue_date__gte=week_ago,
                        invoice__issue_date__lt=today
                    )
                    invoices = invoices.filter(
                        issue_date__gte=week_ago,
                        issue_date__lt=today
                    )
                elif time_frame == 'this_month':
                    sales_data = sales_data.filter(
                        invoice__issue_date__year=today.year,
                        invoice__issue_date__month=today.month
                    )
                    invoices = invoices.filter(
                        issue_date__year=today.year,
                        issue_date__month=today.month
                    )
                elif time_frame == 'last_month':
                    first_day_current_month = today.replace(day=1)
                    last_day_last_month = first_day_current_month - \
                        timedelta(days=1)
                    first_day_last_month = last_day_last_month.replace(day=1)

            total_sales = sales_data.aggregate(
                total_sales=Sum(F('qty') * F('price'))
            )['total_sales'] or Decimal('0.00')

            total_orders = invoices.count()
            avg_order_value = Decimal('0.00')
            if total_orders > 0:
                avg_order_value = invoices.aggregate(
                    avg_value=Sum('total') / total_orders)['avg_value'] or Decimal('0.00')

            # Aggregate totals by product category name
            category_totals = sales_data.values('product__category__category_name').annotate(
                total=Sum(F('qty') * F('price'))
            )

            # Map raw category names into predefined buckets
            buckets = {
                'Electronics': Decimal('0.00'),
                'Clothing': Decimal('0.00'),
                'Home & Garden': Decimal('0.00'),
                'Book': Decimal('0.00'),
                'Other': Decimal('0.00'),
            }

            for item in category_totals:
                cname = (item.get('product__category__category_name')
                         or '').lower()
                total = item.get('total') or Decimal('0.00')

                if 'elect' in cname or 'gadget' in cname or 'phone' in cname or 'laptop' in cname:
                    buckets['Electronics'] += total
                elif 'cloth' in cname or 'apparel' in cname or 'fashion' in cname:
                    buckets['Clothing'] += total
                elif 'home' in cname or 'garden' in cname or 'furnitur' in cname or 'appliance' in cname:
                    buckets['Home & Garden'] += total
                elif 'book' in cname or 'books' in cname:
                    buckets['Book'] += total
                else:
                    buckets['Other'] += total

            # Compute total across buckets and build category data with percentages
            total_in_buckets = sum(buckets.values()) or Decimal('0.00')

            sales_by_category = []
            for k, v in buckets.items():
                total_val = v or Decimal('0.00')
                total_display = float(round(total_val, 2))
                if total_in_buckets and total_in_buckets > Decimal('0.00'):
                    percentage = float(round((total_val / total_in_buckets) * 100, 2))
                else:
                    percentage = 0.0
                sales_by_category.append({
                    'category': k,
                    'total_sales': total_display,
                    'percentage': percentage,
                })

            # Compare total sales to last calendar month
            today = timezone.localdate()
            first_day_current_month = today.replace(day=1)
            last_day_last_month = first_day_current_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)

            last_month_items = products_models.InvoiceItems.objects.filter(
                invoice__user=user,
                invoice__invoice_type="sales",
                invoice__is_deleted=False,
                product__is_deleted=False,
                invoice__issue_date__gte=first_day_last_month,
                invoice__issue_date__lte=last_day_last_month,
            )

            last_month_total = last_month_items.aggregate(
                total_sales=Sum(F('qty') * F('price'))
            )['total_sales'] or Decimal('0.00')

            if last_month_total > Decimal('0.00'):
                percentage_change = float(round(((total_sales - last_month_total) / last_month_total) * 100, 2))
            else:
                percentage_change = 0.0

            # Recent sales: latest invoices (use issue_date then created_at)
            recent_invoices_qs = products_models.Invoice.objects.filter(
                user=user,
                invoice_type="sales",
                is_deleted=False
            ).order_by('-issue_date', '-created_at')[:5]

            recent_sales = []
            for inv in recent_invoices_qs:
                recent_sales.append({
                    'invoice_number': inv.invoice_number,
                    'date': inv.issue_date,
                    'client_name': inv.client.client_name if inv.client else "",
                    'total_amount': inv.total or Decimal('0.00'),
                    'status': inv.status or "",
                })

            data = {
                "total_sales": total_sales,
                "last_month_percentage_change": percentage_change,
                "total_orders": total_orders,
                "avg_order_value": float(round(avg_order_value, 2)),
                "sales_by_category": sales_by_category,
                "recent_sales": recent_sales,
            }

            return Response({"success": True, "message": "Sales summary fetched successfully.", "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OutstandingReceivables(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            client_id = request.query_params.get('client_id')
            as_on_date_str = request.query_params.get('as_on_date')

            as_of = timezone.now().date()
            if as_on_date_str:
                try:
                    from datetime import datetime as _dt
                    as_of = _dt.strptime(as_on_date_str, '%Y-%m-%d').date()
                except Exception:
                    return Response({"success": False, "message": "Invalid as_on_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            invoices = products_models.Invoice.objects.filter(
                user=user, invoice_type="sales", is_deleted=False
            )

            if client_id:
                invoices = invoices.filter(client__client_id=client_id)

            # consider invoices issued on or before the as_of date
            invoices = invoices.filter(
                issue_date__isnull=False, issue_date__lte=as_of)

            # Outstanding invoices (not fully paid)
            outstanding_qs = invoices.exclude(status__iexact="Paid")

            total_outstanding = outstanding_qs.aggregate(
                total=Sum('total')).get('total') or Decimal('0.00')

            # Overdue invoices: due date before today
            overdue_qs = outstanding_qs.filter(payment_due__lt=as_of)
            overdue_amount = overdue_qs.aggregate(
                total=Sum('total')).get('total') or Decimal('0.00')

            # Number of distinct customers with dues
            customers_with_dues = outstanding_qs.exclude(
                client__isnull=True).values('client').distinct().count()

            # Aging buckets
            buckets = {
                'Not due': Decimal('0.00'),
                '0-30': Decimal('0.00'),
                '31-60': Decimal('0.00'),
                '61-90': Decimal('0.00'),
                '90+': Decimal('0.00'),
            }

            for inv in outstanding_qs:
                try:
                    amt = inv.total or Decimal('0.00')
                except Exception:
                    amt = Decimal('0.00')

                if not inv.payment_due:
                    buckets['Not due'] += Decimal(amt)
                else:
                    days = (as_of - inv.payment_due).days
                    if days <= 0:
                        buckets['Not due'] += Decimal(amt)
                    elif 1 <= days <= 30:
                        buckets['0-30'] += Decimal(amt)
                    elif 31 <= days <= 60:
                        buckets['31-60'] += Decimal(amt)
                    elif 61 <= days <= 90:
                        buckets['61-90'] += Decimal(amt)
                    else:
                        buckets['90+'] += Decimal(amt)

            aging = []
            for k, v in buckets.items():
                aging.append({"range": k, "amount": f"{v:.2f}"})

            response = {
                "total_outstanding": f"{Decimal(total_outstanding):.2f}",
                "overdue_amount": f"{Decimal(overdue_amount):.2f}",
                "customers_with_dues": customers_with_dues,
                "aging": aging,
                "detailed_report": [],
            }

            # Build detailed report rows
            detailed = []
            for inv in outstanding_qs.order_by('payment_due'):
                client_name = ""
                try:
                    if inv.client:
                        client_name = getattr(inv.client, 'client_name', '') or getattr(
                            inv.client, 'email', '') or ''
                except Exception:
                    client_name = ""

                amount = inv.total or Decimal('0.00')
                # Since no Payment model exists, derive 'received' from invoice status
                if (inv.status or '').lower() == 'paid':
                    received = amount
                else:
                    received = Decimal('0.00')

                balance = (Decimal(amount) - Decimal(received))

                # aging relative to as_of
                try:
                    aging_days = (
                        as_of - inv.payment_due).days if inv.payment_due else None
                    aging_text = f"{aging_days} days" if aging_days is not None else 'N/A'
                except Exception:
                    aging_text = 'N/A'

                detailed.append({
                    "customer": client_name,
                    "invoice_no": inv.invoice_number or str(inv.invoice_id),
                    "invoice_date": inv.issue_date.strftime('%Y-%m-%d') if inv.issue_date else None,
                    "due_date": inv.payment_due.strftime('%Y-%m-%d') if inv.payment_due else None,
                    "amount": f"{amount:.2f}",
                    "received": f"{received:.2f}",
                    "balance": f"{balance:.2f}",
                    "aging": aging_text
                })

            response['detailed_report'] = detailed

            return Response({"success": True, "message": "Outstanding receivables fetched.", "data": response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PurchaseBySupplier(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Optional filters
            search = request.query_params.get('search')
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')

            orders_qs = products_models.PurchaseOrders.objects.filter(
                user=user, order_type="purchase", is_deleted=False
            )

            if search:
                orders_qs = orders_qs.filter(
                    Q(order_number__icontains=search) |
                    Q(client__client_name__icontains=search) |
                    Q(client__email__icontains=search)
                )

            if from_date:
                try:
                    fd = datetime.strptime(from_date, '%Y-%m-%d').date()
                    orders_qs = orders_qs.filter(order_date__gte=fd)
                except Exception:
                    return Response({"success": False, "message": "Invalid from_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            if to_date:
                try:
                    td = datetime.strptime(to_date, '%Y-%m-%d').date()
                    orders_qs = orders_qs.filter(order_date__lte=td)
                except Exception:
                    return Response({"success": False, "message": "Invalid to_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            # Total purchase amount
            total_purchase = orders_qs.aggregate(
                total=Sum('total')).get('total') or Decimal('0.00')

            # Total items purchased across orders
            total_items_agg = orders_qs.aggregate(
                total_items=Sum('order_items__qty'))
            total_items = int(total_items_agg.get('total_items') or 0)

            # Detailed report rows
            detailed = []
            orders_prefetch = orders_qs.prefetch_related(
                'order_items__product').order_by('-order_date')
            for order in orders_prefetch:
                supplier_name = ''
                try:
                    if order.client:
                        supplier_name = getattr(order.client, 'client_name', '') or getattr(
                            order.client, 'email', '') or ''
                except Exception:
                    supplier_name = ''

                invoice_no = order.order_number or str(order.order_id)
                order_date = order.order_date.strftime(
                    '%Y-%m-%d') if order.order_date else None

                for item in getattr(order, 'order_items').all():
                    item_name = ''
                    item_code = ''
                    try:
                        if item.product:
                            item_name = getattr(item.product, 'name', '') or ''
                            item_code = getattr(
                                item.product, 'item_sku', '') or ''
                    except Exception:
                        pass

                    qty = item.qty or 0
                    rate = item.price or Decimal('0.00')
                    line_total = (Decimal(qty) * Decimal(rate))

                    detailed.append({
                        'supplier': supplier_name,
                        'invoice_no': invoice_no,
                        'date': order_date,
                        'item_name': item_name,
                        'item_code': item_code,
                        'qty': qty,
                        'rate': f"{Decimal(rate):.2f}",
                        'total_amount': f"{line_total:.2f}",
                    })

            response = {
                'total_purchase_amount': f"{Decimal(total_purchase):.2f}",
                'total_items_purchased': total_items,
                'detailed_report': detailed,
            }

            return Response({"success": True, "message": "Purchase by supplier fetched.", "data": response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OutstandingPayables(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            vendor_id = request.query_params.get(
                'vendor_id') or request.query_params.get('supplier_id')
            status_filter = request.query_params.get(
                'status')  # overdue | due_soon | upcoming | all
            search = request.query_params.get('search')
            as_on_date_str = request.query_params.get('as_on_date')
            due_soon_days = request.query_params.get('due_soon_days')

            as_of = timezone.now().date()
            if as_on_date_str:
                try:
                    as_of = datetime.strptime(
                        as_on_date_str, '%Y-%m-%d').date()
                except Exception:
                    return Response({"success": False, "message": "Invalid as_on_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                due_soon_days = int(
                    due_soon_days) if due_soon_days is not None else 7
            except Exception:
                due_soon_days = 7

            invoices = products_models.Invoice.objects.filter(
                user=user, invoice_type="purchase", is_deleted=False)

            # vendor filter
            if vendor_id:
                invoices = invoices.filter(client__client_id=vendor_id)

            # search filter (invoice number or vendor name/email)
            if search:
                invoices = invoices.filter(
                    Q(invoice_number__icontains=search) |
                    Q(client__client_name__icontains=search) |
                    Q(client__email__icontains=search)
                )

            # consider invoices issued on or before as_of
            invoices = invoices.filter(
                issue_date__isnull=False, issue_date__lte=as_of)

            # Outstanding (not paid)
            outstanding_qs = invoices.exclude(status__iexact='Paid')

            # apply status filter if provided
            due_soon_until = as_of + timedelta(days=due_soon_days)
            if status_filter:
                sf = (status_filter or '').lower()
                if sf == 'overdue':
                    outstanding_qs = outstanding_qs.filter(
                        payment_due__lt=as_of)
                elif sf == 'due_soon':
                    outstanding_qs = outstanding_qs.filter(
                        payment_due__gte=as_of, payment_due__lte=due_soon_until)
                elif sf == 'upcoming':
                    outstanding_qs = outstanding_qs.filter(
                        payment_due__gt=due_soon_until)
                # 'all' or unknown -> no extra filtering

            total_payable = outstanding_qs.aggregate(
                total=Sum('total')).get('total') or Decimal('0.00')

            # Overdue: payment_due < as_of
            overdue_qs = outstanding_qs.filter(payment_due__lt=as_of)
            overdue_amount = overdue_qs.aggregate(
                total=Sum('total')).get('total') or Decimal('0.00')

            # Due soon: payment_due between as_of and as_of + due_soon_days
            due_soon_qs = outstanding_qs.filter(
                payment_due__gte=as_of, payment_due__lte=due_soon_until)
            due_soon_amount = due_soon_qs.aggregate(
                total=Sum('total')).get('total') or Decimal('0.00')

            # Aging buckets
            buckets = {
                'Not due': Decimal('0.00'),
                '0-30': Decimal('0.00'),
                '31-60': Decimal('0.00'),
                '61-90': Decimal('0.00'),
                '90+': Decimal('0.00'),
            }

            for inv in outstanding_qs:
                try:
                    amt = inv.total or Decimal('0.00')
                except Exception:
                    amt = Decimal('0.00')

                if not inv.payment_due:
                    buckets['Not due'] += Decimal(amt)
                else:
                    days = (as_of - inv.payment_due).days
                    if days <= 0:
                        buckets['Not due'] += Decimal(amt)
                    elif 1 <= days <= 30:
                        buckets['0-30'] += Decimal(amt)
                    elif 31 <= days <= 60:
                        buckets['31-60'] += Decimal(amt)
                    elif 61 <= days <= 90:
                        buckets['61-90'] += Decimal(amt)
                    else:
                        buckets['90+'] += Decimal(amt)

            aging = [{"range": k, "amount": f"{v:.2f}"}
                     for k, v in buckets.items()]

            # Detailed report
            detailed = []
            for inv in outstanding_qs.order_by('payment_due'):
                vendor = ''
                try:
                    if inv.client:
                        vendor = getattr(inv.client, 'client_name', '') or getattr(
                            inv.client, 'email', '') or ''
                except Exception:
                    vendor = ''

                amount_owed = inv.total or Decimal('0.00')
                status_text = inv.status or ''
                try:
                    aging_days = (
                        as_of - inv.payment_due).days if inv.payment_due else None
                    aging_text = f"{aging_days} days" if aging_days is not None else 'N/A'
                except Exception:
                    aging_text = 'N/A'

                detailed.append({
                    'vendor_name': vendor,
                    'bill_no': inv.invoice_number or str(inv.invoice_id),
                    'bill_date': inv.issue_date.strftime('%Y-%m-%d') if inv.issue_date else None,
                    'due_date': inv.payment_due.strftime('%Y-%m-%d') if inv.payment_due else None,
                    'amount_owed': f"{amount_owed:.2f}",
                    'status': status_text,
                    'aging': aging_text,
                })

            # Grand totals across all purchase invoices (not only filtered)
            grand_total_payables = products_models.Invoice.objects.filter(
                user=user, invoice_type='purchase', is_deleted=False).aggregate(total=Sum('total')).get('total') or Decimal('0.00')
            grand_total_overdue = products_models.Invoice.objects.filter(
                user=user, invoice_type='purchase', is_deleted=False, payment_due__lt=as_of).aggregate(total=Sum('total')).get('total') or Decimal('0.00')

            response = {
                'total_payable': f"{Decimal(total_payable):.2f}",
                'overdue_amount': f"{Decimal(overdue_amount):.2f}",
                'due_soon_amount': f"{Decimal(due_soon_amount):.2f}",
                'aging': aging,
                'detailed_report': detailed,
                'grand_total_payables': f"{Decimal(grand_total_payables):.2f}",
                'grand_total_overdue': f"{Decimal(grand_total_overdue):.2f}",
            }

            return Response({"success": True, "message": "Outstanding payables fetched.", "data": response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProfitAndLossReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            # date filters
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')

            from_date_obj = None
            to_date_obj = None
            try:
                if from_date:
                    from_date_obj = datetime.strptime(
                        from_date, '%Y-%m-%d').date()
                if to_date:
                    to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            except Exception:
                return Response({"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            # Revenue: sum of sales invoices in period
            invoices = products_models.Invoice.objects.filter(
                user=user, invoice_type='sales', is_deleted=False)
            if from_date_obj:
                invoices = invoices.filter(issue_date__gte=from_date_obj)
            if to_date_obj:
                invoices = invoices.filter(issue_date__lte=to_date_obj)

            sales_income = invoices.aggregate(
                total=Sum('total')).get('total') or Decimal('0.00')

            # Service revenue / other income: not explicitly tracked; default to 0.00
            service_revenue = Decimal('0.00')
            other_income = Decimal('0.00')

            total_revenue = Decimal(
                sales_income) + Decimal(service_revenue) + Decimal(other_income)

            # COGS: opening stock and closing stock approximated from current product stock levels * cost_price
            products_qs = products_models.Products.objects.filter(user=user)
            opening_stock = Decimal('0.00')
            closing_stock = Decimal('0.00')
            for p in products_qs:
                try:
                    stock_level = Decimal(p.stock_level or 0)
                    cost_price = Decimal(getattr(p, 'cost_price', 0) or 0)
                    stock_value = stock_level * cost_price
                except Exception:
                    stock_value = Decimal('0.00')
                opening_stock += stock_value
                closing_stock += stock_value

            # Purchases in period
            purchases_qs = products_models.PurchaseOrders.objects.filter(
                user=user, order_type='purchase', is_deleted=False)
            if from_date_obj:
                purchases_qs = purchases_qs.filter(
                    order_date__gte=from_date_obj)
            if to_date_obj:
                purchases_qs = purchases_qs.filter(order_date__lte=to_date_obj)
            purchases_total = purchases_qs.aggregate(
                total=Sum('total')).get('total') or Decimal('0.00')

            total_cogs = Decimal(purchases_total) + \
                Decimal(opening_stock) - Decimal(closing_stock)

            gross_profit = Decimal(total_revenue) - Decimal(total_cogs)

            # Operating expenses by category (rent, salaries, marketing, utilities)
            expenses_qs = users_models.UserExpense.objects.filter(user=user)
            if from_date_obj:
                expenses_qs = expenses_qs.filter(
                    expense_date__gte=from_date_obj)
            if to_date_obj:
                expenses_qs = expenses_qs.filter(expense_date__lte=to_date_obj)

            rent = expenses_qs.filter(category__iexact='rent').aggregate(
                total=Sum('amount')).get('total') or Decimal('0.00')
            salaries = expenses_qs.filter(category__iexact='salaries').aggregate(
                total=Sum('amount')).get('total') or Decimal('0.00')
            marketing = expenses_qs.filter(category__iexact='marketing').aggregate(
                total=Sum('amount')).get('total') or Decimal('0.00')
            utilities = expenses_qs.filter(category__iexact='utilities').aggregate(
                total=Sum('amount')).get('total') or Decimal('0.00')

            total_operating_expense = Decimal(
                rent) + Decimal(salaries) + Decimal(marketing) + Decimal(utilities)

            net_profit = Decimal(gross_profit) - \
                Decimal(total_operating_expense)

            response = {
                'sales_income': f"{Decimal(sales_income):.2f}",
                'service_revenue': f"{Decimal(service_revenue):.2f}",
                'other_income': f"{Decimal(other_income):.2f}",
                'total_revenue': f"{Decimal(total_revenue):.2f}",
                'opening_stock': f"{Decimal(opening_stock):.2f}",
                'purchases': f"{Decimal(purchases_total):.2f}",
                'closing_stock': f"{Decimal(closing_stock):.2f}",
                'total_cogs': f"{Decimal(total_cogs):.2f}",
                'gross_profit': f"{Decimal(gross_profit):.2f}",
                'rent': f"{Decimal(rent):.2f}",
                'salaries': f"{Decimal(salaries):.2f}",
                'marketing': f"{Decimal(marketing):.2f}",
                'utilities': f"{Decimal(utilities):.2f}",
                'total_operating_expense': f"{Decimal(total_operating_expense):.2f}",
                'net_profit': f"{Decimal(net_profit):.2f}",
                'breakdown': [
                    {"category": "Revenue",
                        "amount": f"{Decimal(total_revenue):.2f}"},
                    {"category": "COGS",
                        "amount": f"{Decimal(total_cogs):.2f}"},
                    {"category": "Expense",
                        "amount": f"{Decimal(total_operating_expense):.2f}"},
                    {"category": "Net Profit",
                        "amount": f"{Decimal(net_profit):.2f}"},
                ],
            }

            return Response({"success": True, "message": "Profit and Loss report fetched.", "data": response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CashFlowReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            # date filters
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')

            from_date_obj = None
            to_date_obj = None
            try:
                if from_date:
                    from_date_obj = datetime.strptime(
                        from_date, '%Y-%m-%d').date()
                if to_date:
                    to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            except Exception:
                return Response({"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            # Cash from sales: sum of paid sales invoices within period
            paid_sales_qs = products_models.Invoice.objects.filter(
                user=user, invoice_type='sales', status__iexact='Paid', is_deleted=False)
            if from_date_obj:
                paid_sales_qs = paid_sales_qs.filter(
                    issue_date__gte=from_date_obj)
            if to_date_obj:
                paid_sales_qs = paid_sales_qs.filter(
                    issue_date__lte=to_date_obj)
            cash_from_sales = paid_sales_qs.aggregate(
                total=Sum('total')).get('total') or Decimal('0.00')

            # Payments to suppliers: sum of paid purchase invoices within period
            paid_purchases_qs = products_models.Invoice.objects.filter(
                user=user, invoice_type='purchase', status__iexact='Paid', is_deleted=False)
            if from_date_obj:
                paid_purchases_qs = paid_purchases_qs.filter(
                    issue_date__gte=from_date_obj)
            if to_date_obj:
                paid_purchases_qs = paid_purchases_qs.filter(
                    issue_date__lte=to_date_obj)
            payments_to_suppliers = paid_purchases_qs.aggregate(
                total=Sum('total')).get('total') or Decimal('0.00')

            # Net cash from operating activities approximated: cash from sales - payments to suppliers - operating expenses (paid)
            expenses_qs = users_models.UserExpense.objects.filter(user=user)
            if from_date_obj:
                expenses_qs = expenses_qs.filter(
                    expense_date__gte=from_date_obj)
            if to_date_obj:
                expenses_qs = expenses_qs.filter(expense_date__lte=to_date_obj)
            operating_expenses_paid = expenses_qs.aggregate(
                total=Sum('amount')).get('total') or Decimal('0.00')

            net_cash_operating = Decimal(
                cash_from_sales) - Decimal(payments_to_suppliers) - Decimal(operating_expenses_paid)

            # Investing activities: models not present for equipment/investments -> accept query params or default to 0
            purchase_of_equipment = Decimal(
                request.query_params.get('purchase_of_equipment') or '0.00')
            sales_of_investment = Decimal(
                request.query_params.get('sales_of_investment') or '0.00')
            net_cash_investing = Decimal(
                sales_of_investment) - Decimal(purchase_of_equipment)

            # Financing activities: accept query params for proceeds from loans and dividend payments
            proceeds_from_loans = Decimal(
                request.query_params.get('proceeds_from_loans') or '0.00')
            dividend_payments = Decimal(
                request.query_params.get('dividend_payments') or '0.00')
            net_cash_financing = Decimal(
                proceeds_from_loans) - Decimal(dividend_payments)

            net_cash_flow = Decimal(
                net_cash_operating) + Decimal(net_cash_investing) + Decimal(net_cash_financing)

            response = {
                'cash_from_sales': f"{Decimal(cash_from_sales):.2f}",
                'payments_to_suppliers': f"{Decimal(payments_to_suppliers):.2f}",
                'net_cash_operating_activities': f"{Decimal(net_cash_operating):.2f}",
                'purchase_of_equipment': f"{Decimal(purchase_of_equipment):.2f}",
                'sales_of_investment': f"{Decimal(sales_of_investment):.2f}",
                'net_cash_investing_activities': f"{Decimal(net_cash_investing):.2f}",
                'proceeds_from_loans': f"{Decimal(proceeds_from_loans):.2f}",
                'dividend_payments': f"{Decimal(dividend_payments):.2f}",
                'net_cash_financing_activities': f"{Decimal(net_cash_financing):.2f}",
                'net_cash_flow': f"{Decimal(net_cash_flow):.2f}",
                'breakdown': [
                    {'category': 'Operating',
                        'total': float(net_cash_operating)},
                    {'category': 'Investing',
                        'total': float(net_cash_investing)},
                    {'category': 'Financing',
                        'total': float(net_cash_financing)},
                ],
            }

            return Response({"success": True, "message": "Cash flow report fetched.", "data": response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            # Base querysets
            sales_qs = products_models.Invoice.objects.filter(user=user, invoice_type="sales")
            purchase_qs = products_models.Invoice.objects.filter(user=user, invoice_type="purchase")

            if start_date:
                sales_qs = sales_qs.filter(issue_date__gte=start_date)
                purchase_qs = purchase_qs.filter(issue_date__gte=start_date)
            if end_date:
                sales_qs = sales_qs.filter(issue_date__lte=end_date)
                purchase_qs = purchase_qs.filter(issue_date__lte=end_date)

            # Paid and unpaid splits
            paid_sales = sales_qs.filter(status__iexact="Paid")
            paid_purchases = purchase_qs.filter(status__iexact="Paid")

            # Cash (approximation): cash receipts - cash paid (paid purchases + expenses)
            cash_in = paid_sales.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            cash_out_purchases = paid_purchases.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            total_expense = users_models.UserExpense.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            cash = Decimal(cash_in) - (Decimal(cash_out_purchases) + Decimal(total_expense))

            # Inventory: sum(stock_level or quantity) * cost_price
            inventory = Decimal('0.00')
            products_qs = products_models.Products.objects.filter(user=user)
            for p in products_qs:
                qty = p.quantity if p.quantity is not None else (p.stock_level or 0)
                cost = p.cost_price or Decimal('0.00')
                try:
                    inventory += Decimal(qty or 0) * Decimal(cost)
                except Exception:
                    pass

            # Accounts receivable: unpaid sales invoices
            accounts_receivable = sales_qs.exclude(status__iexact="Paid").aggregate(total=Sum('total'))['total'] or Decimal('0.00')

            # Fixed assets (PP&E) - accept via query param if no dedicated model
            fixed_assets = Decimal(request.query_params.get('fixed_assets') or '0.00')

            total_assets = Decimal(cash) + Decimal(inventory) + Decimal(accounts_receivable) + Decimal(fixed_assets)

            # Liabilities
            accounts_payable = purchase_qs.exclude(status__iexact="Paid").aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            short_term_debt = Decimal(request.query_params.get('short_term_debt') or '0.00')
            long_term_loans = Decimal(request.query_params.get('long_term_loans') or '0.00')

            # Equity
            owners_capital = Decimal(request.query_params.get('owners_capital') or '0.00')

            # Retained earnings (approx): cumulative profit = revenue - cogs - expenses
            cogs = products_models.InvoiceItems.objects.filter(invoice__in=paid_sales).aggregate(total_cogs=Sum(F('qty') * F('product__cost_price')))['total_cogs'] or Decimal('0.00')
            retained_earnings = Decimal(cash_in) - Decimal(cogs) - Decimal(total_expense)

            total_equity = owners_capital + Decimal(retained_earnings)

            total_liabilities_and_equity = Decimal(accounts_payable) + Decimal(short_term_debt) + Decimal(long_term_loans) + Decimal(total_equity)

            data = {
                'cash': f"{Decimal(cash):.2f}",
                'inventory': f"{Decimal(inventory):.2f}",
                'accounts_receivable': f"{Decimal(accounts_receivable):.2f}",
                'fixed_assets': f"{Decimal(fixed_assets):.2f}",
                'total_assets': f"{Decimal(total_assets):.2f}",
                'accounts_payable': f"{Decimal(accounts_payable):.2f}",
                'short_term_debt': f"{Decimal(short_term_debt):.2f}",
                'long_term_loans': f"{Decimal(long_term_loans):.2f}",
                'owners_capital': f"{Decimal(owners_capital):.2f}",
                'retained_earnings': f"{Decimal(retained_earnings):.2f}",
                'total_equity': f"{Decimal(total_equity):.2f}",
                'total_liabilities_and_equity': f"{Decimal(total_liabilities_and_equity):.2f}",
            }

            return Response({"success": True, "message": "Balance sheet fetched.", "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)    
    

class TaxOnSalesReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            sales_qs = products_models.Invoice.objects.filter(user=user, invoice_type='sales', status__iexact='Paid', is_deleted=False)
            if start_date:
                sales_qs = sales_qs.filter(issue_date__gte=start_date)
            if end_date:
                sales_qs = sales_qs.filter(issue_date__lte=end_date)

            total_tax_invoices = sales_qs.aggregate(total=Sum('tax'))['total'] or Decimal('0.00')
            total_revenue = sales_qs.aggregate(total=Sum('total'))['total'] or Decimal('0.00')

            items_qs = products_models.InvoiceItems.objects.filter(invoice__in=sales_qs)
            total_tax_items = items_qs.aggregate(total=Sum('tax'))['total'] or Decimal('0.00')

            # Determine total tax collected (prefer invoice.tax if present)
            total_tax_collected = Decimal(total_tax_invoices) if Decimal(total_tax_invoices) != Decimal('0.00') else Decimal(total_tax_items)

            tax_details = []

            if total_tax_items and total_tax_items != Decimal('0.00'):
                # Sum amounts by gst_category and ensure GST/VAT/Service Tax entries are always present
                grouped = items_qs.values('gst_category').annotate(amount=Sum('tax'))
                gst_amt = Decimal('0.00')
                vat_amt = Decimal('0.00')
                service_amt = Decimal('0.00')
                other_entries = []
                covered_amount = Decimal('0.00')
                for g in grouped:
                    try:
                        rate = g.get('gst_category')
                        amt = Decimal(g.get('amount') or Decimal('0.00'))
                    except Exception:
                        continue

                    covered_amount += amt

                    if rate is None:
                        other_entries.append({"name": "Other Tax", "rate": "", "amount": f"{amt:.2f}"})
                    else:
                        try:
                            r = Decimal(rate)
                        except Exception:
                            other_entries.append({"name": f"Tax @ {rate}", "rate": str(rate), "amount": f"{amt:.2f}"})
                            continue

                        if r == Decimal('5'):
                            gst_amt += amt
                        elif r == Decimal('10'):
                            vat_amt += amt
                        elif r == Decimal('2'):
                            service_amt += amt
                        else:
                            other_entries.append({"name": f"Other Tax", "rate": "-", "amount": f"{amt:.2f}"})

                # Always include GST, VAT, Service Tax entries (may be zero)
                tax_details.append({"name": "GST", "rate": "5%", "amount": f"{gst_amt:.2f}"})
                tax_details.append({"name": "VAT", "rate": "10%", "amount": f"{vat_amt:.2f}"})
                tax_details.append({"name": "Service Tax", "rate": "2%", "amount": f"{service_amt:.2f}"})

                # Append other discovered rates
                for e in other_entries:
                    tax_details.append(e)

                # If invoice-level tax exists beyond item-level tax, include it separately
                invoice_level_extra = Decimal(total_tax_invoices) - covered_amount
                if invoice_level_extra and invoice_level_extra > Decimal('0.00'):
                    tax_details.append({"name": "Invoice-level Tax", "rate": "", "amount": f"{invoice_level_extra:.2f}"})

            else:
                # Fallback: estimate by applying fixed rates to revenue
                gst_amt = (Decimal(total_revenue) * Decimal('0.05')).quantize(Decimal('0.01'))
                vat_amt = (Decimal(total_revenue) * Decimal('0.10')).quantize(Decimal('0.01'))
                service_amt = (Decimal(total_revenue) * Decimal('0.02')).quantize(Decimal('0.01'))
                estimated_sum = gst_amt + vat_amt + service_amt
                other_amt = Decimal('0.00')
                if total_tax_collected and total_tax_collected > estimated_sum:
                    other_amt = total_tax_collected - estimated_sum

                tax_details = [
                    {"name": "GST", "rate": "5%", "amount": f"{gst_amt:.2f}"},
                    {"name": "VAT", "rate": "10%", "amount": f"{vat_amt:.2f}"},
                    {"name": "Service Tax", "rate": "2%", "amount": f"{service_amt:.2f}"},
                ]
                if other_amt > 0:
                    tax_details.append({"name": "Other Tax", "rate": "", "amount": f"{other_amt:.2f}"})

            response = {
                "total_tax_collected": f"{Decimal(total_tax_collected):.2f}",
                "tax_details": tax_details
            }

            # Build month-wise chart data
            try:
                # Determine date range for months
                if start_date and end_date:
                    try:
                        start_dt = datetime.fromisoformat(start_date).date()
                    except Exception:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                    try:
                        end_dt = datetime.fromisoformat(end_date).date()
                    except Exception:
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                else:
                    now = timezone.now().date()
                    start_dt = now.replace(month=1, day=1)
                    end_dt = now.replace(month=12, day=31)

                # Aggregate invoice-level tax per month
                invoice_months = sales_qs.annotate(month=TruncMonth('issue_date')).values('month').annotate(total=Sum('tax'))
                invoice_map = {}
                for im in invoice_months:
                    m = im.get('month')
                    if m:
                        # normalize month key to a date (first day of month)
                        key = m.date() if hasattr(m, 'date') else m
                        invoice_map[key] = Decimal(im.get('total') or Decimal('0.00'))

                # Aggregate item-level tax per month (by invoice issue_date)
                items_months = items_qs.annotate(month=TruncMonth('invoice__issue_date')).values('month').annotate(total=Sum('tax'))
                items_map = {}
                for it in items_months:
                    m = it.get('month')
                    if m:
                        key = m.date() if hasattr(m, 'date') else m
                        items_map[key] = Decimal(it.get('total') or Decimal('0.00'))

                # Build month list from start_dt to end_dt
                chart_data = []
                cur = start_dt.replace(day=1)
                while cur <= end_dt:
                    month_start = cur.replace(day=1)
                    inv_amt = invoice_map.get(month_start, Decimal('0.00'))
                    item_amt = items_map.get(month_start, Decimal('0.00'))
                    # Prefer invoice-level tax when present (non-zero)
                    month_amt = inv_amt if inv_amt and inv_amt != Decimal('0.00') else item_amt
                    chart_data.append({"month": month_start.strftime('%b'), "amount": f"{month_amt:.2f}"})
                    # increment month
                    if cur.month == 12:
                        cur = cur.replace(year=cur.year + 1, month=1)
                    else:
                        cur = cur.replace(month=cur.month + 1)

                # Also provide separate arrays for labels and values
                chart_months = [c.get('month') for c in chart_data]
                chart_amounts = [c.get('amount') for c in chart_data]

                response['chart_months'] = chart_months
                response['chart_amounts'] = chart_amounts
            
            except Exception:
                response['chart_data'] = []

            return Response({"success": True, "message": "Tax on sales report fetched.", "data": response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaxOnPurchaseReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            sales_qs = products_models.Invoice.objects.filter(user=user, invoice_type='purchase', status__iexact='Paid', is_deleted=False)
            if start_date:
                sales_qs = sales_qs.filter(issue_date__gte=start_date)
            if end_date:
                sales_qs = sales_qs.filter(issue_date__lte=end_date)

            total_tax_invoices = sales_qs.aggregate(total=Sum('tax'))['total'] or Decimal('0.00')
            total_revenue = sales_qs.aggregate(total=Sum('total'))['total'] or Decimal('0.00')

            items_qs = products_models.InvoiceItems.objects.filter(invoice__in=sales_qs)
            total_tax_items = items_qs.aggregate(total=Sum('tax'))['total'] or Decimal('0.00')

            # Determine total tax collected (prefer invoice.tax if present)
            total_tax_collected = Decimal(total_tax_invoices) if Decimal(total_tax_invoices) != Decimal('0.00') else Decimal(total_tax_items)

            tax_details = []

            if total_tax_items and total_tax_items != Decimal('0.00'):
                # Sum amounts by gst_category and ensure GST/VAT/Service Tax entries are always present
                grouped = items_qs.values('gst_category').annotate(amount=Sum('tax'))
                gst_amt = Decimal('0.00')
                vat_amt = Decimal('0.00')
                service_amt = Decimal('0.00')
                other_entries = []
                covered_amount = Decimal('0.00')
                for g in grouped:
                    try:
                        rate = g.get('gst_category')
                        amt = Decimal(g.get('amount') or Decimal('0.00'))
                    except Exception:
                        continue

                    covered_amount += amt

                    if rate is None:
                        other_entries.append({"name": "Other Tax", "rate": "", "amount": f"{amt:.2f}"})
                    else:
                        try:
                            r = Decimal(rate)
                        except Exception:
                            other_entries.append({"name": f"Tax @ {rate}", "rate": str(rate), "amount": f"{amt:.2f}"})
                            continue

                        if r == Decimal('5'):
                            gst_amt += amt
                        elif r == Decimal('10'):
                            vat_amt += amt
                        elif r == Decimal('2'):
                            service_amt += amt
                        else:
                            other_entries.append({"name": f"Other Tax", "rate": "-", "amount": f"{amt:.2f}"})

                # Always include GST, VAT, Service Tax entries (may be zero)
                tax_details.append({"name": "GST", "rate": "5%", "amount": f"{gst_amt:.2f}"})
                tax_details.append({"name": "VAT", "rate": "10%", "amount": f"{vat_amt:.2f}"})
                tax_details.append({"name": "Service Tax", "rate": "2%", "amount": f"{service_amt:.2f}"})

                # Append other discovered rates
                for e in other_entries:
                    tax_details.append(e)

                # If invoice-level tax exists beyond item-level tax, include it separately
                invoice_level_extra = Decimal(total_tax_invoices) - covered_amount
                if invoice_level_extra and invoice_level_extra > Decimal('0.00'):
                    tax_details.append({"name": "Invoice-level Tax", "rate": "", "amount": f"{invoice_level_extra:.2f}"})

            else:
                # Fallback: estimate by applying fixed rates to revenue
                gst_amt = (Decimal(total_revenue) * Decimal('0.05')).quantize(Decimal('0.01'))
                vat_amt = (Decimal(total_revenue) * Decimal('0.10')).quantize(Decimal('0.01'))
                service_amt = (Decimal(total_revenue) * Decimal('0.02')).quantize(Decimal('0.01'))
                estimated_sum = gst_amt + vat_amt + service_amt
                other_amt = Decimal('0.00')
                if total_tax_collected and total_tax_collected > estimated_sum:
                    other_amt = total_tax_collected - estimated_sum

                tax_details = [
                    {"name": "GST", "rate": "5%", "amount": f"{gst_amt:.2f}"},
                    {"name": "VAT", "rate": "10%", "amount": f"{vat_amt:.2f}"},
                    {"name": "Service Tax", "rate": "2%", "amount": f"{service_amt:.2f}"},
                ]
                if other_amt > 0:
                    tax_details.append({"name": "Other Tax", "rate": "", "amount": f"{other_amt:.2f}"})

            response = {
                "total_tax_collected": f"{Decimal(total_tax_collected):.2f}",
                "tax_details": tax_details
            }

            return Response({"success": True, "message": "Tax on purchase report fetched.", "data": response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExpenseByCategoryReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            qs = users_models.UserExpense.objects.filter(user=user)
            if start_date:
                qs = qs.filter(expense_date__gte=start_date)
            if end_date:
                qs = qs.filter(expense_date__lte=end_date)

            categories = [
                "Food & Dining",
                "Transport",
                "Shopping",
                "Bills",
                "Entertainment",
            ]

            # collect amounts per category first
            cat_amounts = {}
            for cat in categories:
                amt = qs.filter(category__iexact=cat).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                cat_amounts[cat] = Decimal(amt)

            total_expense = sum(cat_amounts.values(), Decimal('0.00'))

            # simple breakdown (category + amount)
            breakdown = [{"category": cat, "amount": f"{cat_amounts[cat]:.2f}"} for cat in categories]

            # new breakdown: category, percentage, amount
            breakdown_with_percentage = []
            for cat in categories:
                amt = cat_amounts[cat]
                if total_expense > 0:
                    percent = (amt / total_expense) * 100
                else:
                    percent = Decimal('0.00')
                breakdown_with_percentage.append({
                    "category": cat,
                    "percentage": f"{percent:.2f}",
                    "amount": f"{amt:.2f}"
                })

            response = {
                "total_expense": f"{total_expense:.2f}",
                "breakdown": breakdown,
                "breakdown_with_percentage": breakdown_with_percentage
            }

            return Response({"success": True, "message": "Expense by category fetched.", "data": response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExpenseByDateReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            qs = users_models.UserExpense.objects.filter(user=user)
            if start_date:
                qs = qs.filter(expense_date__gte=start_date)
            if end_date:
                qs = qs.filter(expense_date__lte=end_date)


            total_expense = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            # current week breakdown (Monday -> Sunday)
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_details = []
            for i in range(7):
                d = week_start + timedelta(days=i)
                amt = qs.filter(expense_date=d).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                week_details.append({
                    "date": d.isoformat(),
                    "day": d.strftime("%A"),
                    "amount": f"{Decimal(amt):.2f}"
                })

            response = {
                "total_expense": f"{Decimal(total_expense):.2f}",
                "current_week": week_details
            }

            return Response({"success": True, "message": "Expense by date fetched.", "data": response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

