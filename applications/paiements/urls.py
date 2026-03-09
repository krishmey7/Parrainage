from django.urls import path
from . import views



urlpatterns = [
    #path('depot/', views.vue_depot, name='depot'),
    path('retrait/', views.vue_retrait, name='retrait'),
    path('liste-depots/', views.liste_depots, name='liste_depots'),
    path('liste-retraits/', views.liste_retraits, name='liste_retraits'),  # Assurez-vous que cette ligne est présente
]
