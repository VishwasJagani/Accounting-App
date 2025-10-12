# Rest Framework
from rest_framework_simplejwt.tokens import RefreshToken

# Django
from django.core.mail import send_mail


def is_required(value):
    return value in ["", None]


def get_user_token(user_instance):
    """
    Get the refresh and access tokens for the user.
    """
    if user_instance:
        refresh = RefreshToken.for_user(user_instance)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    return None


def is_valid_image(file):
    """
    Check if the uploaded file is a valid image.
    """
    try:
        extension = file.name.split('.')[-1]
        if extension.lower() not in ['jpg', 'jpeg', 'png']:
            return False

        return True

    except Exception as e:
        return False


def send_mail(data):
    """
    Send an email using the provided data.
    """
    # Implement email sending logic here
    pass