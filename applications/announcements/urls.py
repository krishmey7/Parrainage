from django.urls import path
from . import views

app_name = "announcements"

urlpatterns = [
    path("", views.home_announcements, name="home"),
    path("public/", views.public_announcements, name="public_list"),
    path("personal/", views.personal_announcements, name="personal_list"),
]
