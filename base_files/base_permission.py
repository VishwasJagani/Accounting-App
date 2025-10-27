import jwt

# Django
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

# Rest Framework
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

# Local
from users import models as users_models



class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            raise PermissionDenied(
                "Authorization header not provided or not in the correct format.", code=403)

        token = auth_header.split(' ')[1]

        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = decoded_token.get('user_id')

            if user_id is not None:
                user_instance = users_models.User.objects.select_related('user_role').filter(
                    user_id=user_id, is_deleted=False)

                if user_instance.exists():
                    request.user_id = user_id
                    request.user = user_instance.first()
                    if not request.user.is_active:
                        raise PermissionDenied(
                            "Your account is inactive. Please contact support.", code=403)
                    return True
                else:
                    raise PermissionDenied("User not found.", code=403)
            else:
                raise PermissionDenied(
                    "User id not present in the token.", code=403)
        except jwt.ExpiredSignatureError:
            raise PermissionDenied("Token has expired.", code=403)
        except jwt.InvalidTokenError:
            raise PermissionDenied("Invalid token.", code=403)
