from django.urls import path
from . import views

urlpatterns = [
    path('inscription/', views.vue_inscription, name='inscription'),
    path('ajouter-parrain/', views.vue_ajouter_code_parrain, name='ajouter_parrain'),
]
