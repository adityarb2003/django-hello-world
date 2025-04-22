# example/urls.py
# from django.urls import path

# from example.views import index


# urlpatterns = [
#     path('', index),
# ]
# hackernews/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import auth_views as custom_auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('newest/', views.newest, name='newest'),
    path('submit/', views.submit_story, name='submit_story'),
    path('story/<int:pk>/', views.story_detail, name='story_detail'),
    path('upvote/<int:pk>/', views.upvote_story, name='upvote_story'),
    path('comment/<int:story_pk>/', views.submit_comment, name='submit_comment'),
    path('comment/<int:story_pk>/<int:parent_pk>/', views.submit_comment, name='submit_reply'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('search/', views.search, name='search'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', custom_auth_views.register, name='register'),
]