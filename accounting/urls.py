"""
URL configuration for accounting project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# Django
from drf_yasg import openapi
from django.conf import settings
from django.contrib import admin
from rest_framework import permissions
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from django.urls import include, path, re_path


schema_view = get_schema_view(
   openapi.Info(
      title="Accounting Project API",
      default_version='v1',
      description="API documentation for Accounting project",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="support@myproject.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   url = "https://miguelina-untrod-werner.ngrok-free.dev"
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include([
        path('user/', include('users.urls')),
        path('product/', include('products.urls')),
        path('admin_panel/', include('admin_panel.urls')),

    ])),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger',
        cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc',
        cache_timeout=0), name='schema-redoc'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)