# Django
from django.urls import path, include

# Local
from users import views as users_views


urlpatterns = [

    path('role-list/', users_views.RoleList.as_view(), name="role-list"),

    path('register/', users_views.RegisterView.as_view(), name="register"),
    path('login/', users_views.LoginView.as_view(), name="login"),
    path('profile/', users_views.UserProfileView.as_view(), name="user_profile"),

    path('change-password/', users_views.ChangePasswordView.as_view(),
         name="change-password"),

    path('send-otp/', users_views.SendOTPView.as_view(),
         name="send-otp"),
    path('verify-otp/', users_views.VerifyOTPView.as_view(),
         name="verify-otp"),

    path('client/', include([
        path('', users_views.ClientView.as_view(), name='client-list'),
        path('add/', users_views.AddClientView.as_view(), name='add-client'),
        path('details/<int:client_id>',
             users_views.ClientDetailView.as_view(), name='client-details'),
        path('add-remove-favorite/<int:client_id>',
             users_views.AddRemoveFavoriteClient.as_view(), name='add-remove-favorite-client'),
        path('<int:client_id>/invoices',
             users_views.InvoiceListByClientID.as_view(), name='add-remove-favorite-client'),
    ])),

    path('user-login-history/', users_views.UserLoginHistory.as_view(),
         name="user-login-history"),

    path('user-company/', users_views.UserCompany.as_view(),
         name="user-company"),

    path('get-info-from-gst-number/', users_views.GetInfoFromGSTNumber.as_view(),
         name="get-info-from-gst-number"),

    path('expense/', include([
         path('', users_views.UserExpenseList.as_view(), name="expense_list"),
         path('add/', users_views.AddUserExpense.as_view(), name="add_expense"),
         path('report/', users_views.ExpenseReportPage.as_view(),
              name="expense_report"),
         ])),

    path('statistics-page/', users_views.StatisticsPageView.as_view(),
         name="statistics_page"),
    path('reports/', include([
         path('sales-by-client', users_views.SalesByClientReportView.as_view(),
              name="sales-by-client-report"),
         path('sales-by-product', users_views.SalesByProductView.as_view(),
              name="sales-by-product-report"),
         path('sales-by-date-range', users_views.SalesByDateRange.as_view(),
              name="sales-by-product-report"),
         path('sales-summary', users_views.SalesSummaryView.as_view(),
              name="sales-summary"),
         ])),
]
