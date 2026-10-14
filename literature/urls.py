from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('authors/<slug:slug>/', views.author_detail, name='author'),
    path('materials/<int:pk>/', views.material_stream, name='material-stream'),
    path('materials/<int:pk>/download/', views.material_download, name='material-download'),
]
