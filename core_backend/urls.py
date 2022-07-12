from django.contrib import admin
from django.shortcuts import render
from django.urls import path, re_path, include

def front(request):
    return render(request, "index.html", {})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('core_api.urls')),
    re_path(r'.*', front),
]
