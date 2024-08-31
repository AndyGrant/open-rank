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
]
