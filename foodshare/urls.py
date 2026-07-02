from django.contrib import admin
from django.urls import path
from core import views
from django.contrib.auth import views as av

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/<int:pk>/like/', views.recipe_like, name='recipe_like'),
    path('recipes/<int:pk>/save/', views.recipe_save, name='recipe_save'),
    path('recipes/add/', views.add_recipe, name='add_recipe'),
    path('recipes/<int:pk>/delete/', views.delete_recipe, name='delete_recipe'),
    path('ai-kitchen/', views.ai_kitchen, name='ai_kitchen'),
    path('chat/', views.chat, name='chat'),
 path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('login/', av.LoginView.as_view(template_name='login.html'), name='login'),
path('logout/', views.logout_view, name='logout'),]
