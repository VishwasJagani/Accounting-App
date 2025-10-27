# Django
import os
from drf_yasg import openapi
from django.db.models import Q
from django.utils import timezone
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
        return users_models.ClientModel.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-created_at')

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

                serializer = self.serializer_class(client).data
                return Response({"success": True, "message": "Client fetched successfully.", "data": serializer}, status=status.HTTP_200_OK)

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
