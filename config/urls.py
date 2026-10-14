from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url=static_url('img/favicon.ico'), permanent=True)),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('literature.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
