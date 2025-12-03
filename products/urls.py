# Django
from django.urls import path, include

# Local
from products import views as products_views


urlpatterns = [

    path('product-category/', include([
        path('', products_views.ProductCategoryListView.as_view(),
             name='product-category-list'),
        path('add/', products_views.AddProductCategory.as_view(),
             name='add-product-category'),
        path('details/<int:category_id>',
             products_views.ProductCategoryDetailView.as_view(), name='product-category-details'),
    ])),

    path('products/', include([
        path('', products_views.ProductListView.as_view(),
             name='product-list'),
        path('add/', products_views.AddProductView.as_view(),
             name='add-product'),
        path('details/<int:product_id>', products_views.ProductDetailsView.as_view(),
             name='product-details'),
    ])),

    path('purchase-order/', include([
        path('', products_views.PurchaseOrderListView.as_view(),
             name="purchase-order-list"),
         path('add/', products_views.CreatePurchaseOrderView.as_view(),
              name="add-purchase-order"),
         path('details/<int:order_id>', products_views.PurchaseOrderDetailView.as_view(),
              name="details-purchase-order"),
         ])),

    path('invoice/', include([
         path('', products_views.InvoiceListView.as_view(), name='add-invoice'),
         path('add/', products_views.AddInvoiceView.as_view(), name='add-invoice'),
         path('details/<int:invoice_id>',
              products_views.InvoiceOrderDetailView.as_view(), name='add-invoice'),
         ])),

    path('home-page/', products_views.HomePageView.as_view(), name='home_page'),
]
