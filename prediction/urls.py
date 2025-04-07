from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_file, name='upload'),
    path('predict/', views.predict_weight_ajax, name='predict_ajax'),
    path('delete/<int:fish_id>/', views.delete_fish, name='delete_fish'),
    path('predict/upload/', views.predict_from_upload, name='predict_from_upload'),
    path('update_weight/<int:fish_id>/', views.update_weight, name='update_weight'),
]