from django.urls import path, include

from openrank import views

urlpatterns = [
    path('', views.index, name='index'),

    path('family/create/', views.create_or_edit_family, name='admin_family'),
    path('family/edit/<int:pk>/', views.create_or_edit_family, name='admin_family'),
    path('family/list/', views.list_families, name='list_families'),

    path('engine/create/', views.create_or_edit_engine, name='admin_engine'),
    path('engine/edit/<int:pk>/', views.create_or_edit_engine, name='admin_engine'),
    path('engine/list/', views.list_engines,name='list_engines'),

    path('rating-list/create/', views.create_or_edit_rating_list, name='admin_rating_list'),
    path('rating-list/edit/<int:pk>/', views.create_or_edit_rating_list, name='admin_rating_list'),
    path('rating-list/list/', views.list_rating_lists,name='list_rating_lists'),

    path('pairings/<int:pk1>/edit/<int:pk2>/', views.create_or_edit_pairing, name='admin_pairing'),
    path('pairings/<int:pk>/list/', views.list_pairings, name='list_pairings'),
    path('pairings/<int:pk>/generate/primary/', views.generate_primary_pairings, name='generate_primary_pairings'),
]
