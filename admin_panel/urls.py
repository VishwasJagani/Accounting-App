# Django
from django.urls import path, include

# Local
from admin_panel import views as admin_panel_views


urlpatterns = [

    path('users/', include([
        path('', admin_panel_views.UserListView.as_view(), name='user-list'),
        path('details/<int:user_id>',
             admin_panel_views.UserDetailView.as_view(), name='user-list'),
    ]))

]
