from django.urls import path, include
from . import views

urlpatterns = [

    path('', views.index, name='index'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', views.signup, name='signup'),

    # General Admin Views, not intended for distribution

    path('families/', views.family_list, name='family_list'),
    path('families/new/', views.family_create, name='family_create'),
    path('families/<int:family_id>/engines/', views.family_engines, name='family_engines'),

    path('engines/new/', views.engine_create, name='engine_create'),
    path('engines/edit/<int:engine_id>', views.engine_edit, name='engine_edit'),
    path('engines/new/<int:family_id>/', views.engine_create, name='engine_create_for_family'),
    path('engines/<int:engine_id>/add_to_list/<int:list_id>', views.engine_add_to_list, name='engine_add_to_list'),

    path('lists/', views.rating_list_list, name='rating_list_list'),
    path('lists/new/', views.rating_list_create, name='rating_list_create'),
    path('lists/<int:rating_list_id>/stages/new/', views.rating_list_stage_create, name='rating_list_stage_create'),
    path('lists/<int:stage_id>/pairings/', views.pairings_for_stage, name='stage_pairings'),
    path('lists/<int:stage_id>/generate_pairings/', views.pairings_generate, name='generate_pairings'),

    # Client Views

    path('client/connect/', views.client_connect, name='client_connect'),
    path('client/request_work/', views.client_request_work, name='client_request_work'),
    path('client/pull_fastchess/', views.client_pull_fastchess, name='client_pull_fastchess'),
    path('client/pull_image/', views.client_pull_image, name='client_pull_image'),
    path('client/pull_book/', views.client_pull_book, name='client_pull_book'),
]
