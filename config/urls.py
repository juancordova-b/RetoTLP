from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import TemplateView


def health_check(request):
    return JsonResponse(
        {
            "status": "ok",
            "proyecto": "FairBet Lab",
        }
    )


urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("cuenta/", TemplateView.as_view(template_name="cuenta.html"), name="cuenta"),
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health"),
    path("api/users/", include("apps.users.urls")),
]
