from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("api/users/", include("users.urls")),
    path("api/wallets/", include("wallets.urls")),
    path("api/tokens/", include("tokens.urls")),
]
