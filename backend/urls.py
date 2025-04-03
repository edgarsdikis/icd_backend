from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("api/users/", include("users.urls")),
    path("api/", include("portfolio.urls")),  # This replaces wallets and tokens URLs
]
