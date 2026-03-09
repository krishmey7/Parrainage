from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls.i18n import i18n_patterns



urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('applications.noyau.urls')),
    path('comptes/', include('applications.comptes.urls')),
    path('portefeuille/', include('applications.portefeuille.urls')),

    path('paiements/', include('applications.paiements.urls')),
    path('produits/', include('applications.produits.urls')),
    path('parrainages/', include('applications.parrainages.urls')),
    path('shop/', include('applications.shop.urls')),
    path('service_client', include('applications.service_client.urls')),
    path('announcements/', include('applications.announcements.urls')),

    path('gestion_bonana/', include('applications.gestion_bonana.urls')),


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('i18n/', include('django.conf.urls.i18n')),
]
from django.contrib import admin

# Changer les textes affichés
admin.site.site_header = "Admin Genius"
admin.site.site_title = "Admin Genius"
admin.site.index_title = "Bienvenue sur l’espace de gestion"
