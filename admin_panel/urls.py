# Django
from django.urls import path, include

# Local
from admin_panel import views as admin_panel_views

urlpatterns = [

    path('users/', include([
        path('', admin_panel_views.UserListView.as_view(), name='user-list'),
        path('details/<int:user_id>',
             admin_panel_views.UserDetailView.as_view(), name='user-list'),
    ])),

    path('faqs/', include([
        path('add/', admin_panel_views.AddFAQsView.as_view(), name='add-faq'),
        path('list/', admin_panel_views.FAQsListView.as_view(), name='faq-list'),
        path('details/<int:faq_id>/',
             admin_panel_views.FAQDetailView.as_view(), name='faq-detail'),
    ])),

    path('terms-and-conditions/', include([
        path('add/', admin_panel_views.AddTermsAndConditionsView.as_view(),
             name='add-terms-and-conditions'),
        path('get-terms-and-conditions/', admin_panel_views.GetTermsAndConditionsView.as_view(),
             name='get-terms-and-conditions'),
        path('details/<int:terms_and_conditions_id>/',
             admin_panel_views.TermsAndConditionsDetailView.as_view(), name='terms-and-conditions-detail'),
    ])),

    path('contact-us/', include([
        path('add/', admin_panel_views.AddContactUsView.as_view(),
             name='add-contact-us'),
        path('get-contact-us/', admin_panel_views.GetContactUsView.as_view(),
             name='get-contact-us'),
        path('details/<int:contact_us_id>/',
             admin_panel_views.ContactUsDetailView.as_view(), name='contact-us-detail'),
    ])),

    path('inquiries/', include([
        path('list/', admin_panel_views.InquiryListView.as_view(),
             name='inquiry-list'),
    ])),

    path('about-us/', include([
        path('add/', admin_panel_views.AddAboutUsView.as_view(),
             name='add-about-us'),
        path('get-about-us/', admin_panel_views.GetAboutUsView.as_view(),
             name='get-about-us'),
        path('details/<int:about_us_id>/',
             admin_panel_views.AboutUsDetailView.as_view(), name='about-us-detail'),
    ])),


]
