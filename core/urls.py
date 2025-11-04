from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('delete_file/<int:file_id>/', views.delete_file, name='delete_file'),

    # La URL pública para visualizar archivos
    path('<slug:area_slug>/<slug:file_slug>/', views.serve_file, name='serve_file'),
]