from django.contrib import admin
from django.urls import path, re_path, include

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('core_api.urls')),
    re_path(r'.*', views.front),
]
