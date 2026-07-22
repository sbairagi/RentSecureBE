"""
URL configuration for rentsecure_be project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from payments.views.bank_views import update_owner_bank_details

urlpatterns: list[object] = [
    path("admin/", admin.site.urls),
    path("api/webhook/", include("payments.urls")),
    path("api/", include("core.urls")),
    path("api/", include("properties.urls")),
    path("api/notifications/", include("notification.urls")),
    path("api/owner/update-bank-details/", update_owner_bank_details),
    path("properties/", include("properties.urls")),
    path("documents/", include("documents.urls")),
]


# Add this to serve media files in development
if settings.DEBUG:
    urlpatterns = urlpatterns + static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
