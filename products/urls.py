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
    ]))

]
