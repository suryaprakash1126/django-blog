from django.urls import path
from . views import *

urlpatterns = [
    path('', public_portfolio, name='portfolio'),
    path('explore/', explore_view, name='explore'),
    path('blog/list/',list,name='blog_list'),
    path('blog/create/', create_blog_post_form, name='create_blog_post_form'),
    path('blog/detail/<int:post_id>/',detail,name='blog_detail'),
    path('post/<int:post_id>/like/', toggle_like, name='toggle_like'),
    path('blog/<int:post_id>/edit/', blog_update, name='blog_update'),
    path('blog/<int:post_id>/delete/', blog_delete, name='blog_delete'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/download-pdf/', download_my_posts_pdf, name='download_my_posts_pdf'),

]