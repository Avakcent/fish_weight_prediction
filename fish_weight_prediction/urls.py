from django.contrib import admin
from django.urls import path, include  # Импортируйте include

urlpatterns = [
    path('admin/', admin.site.urls),  # Админка Django
    path('', include('prediction.urls')),  # Подключите URL-адреса приложения prediction
]