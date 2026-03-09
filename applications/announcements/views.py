from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Announcement

@login_required
def home_announcements(request):
    """
    Page d'accueil des annonces : affiche un aperçu des annonces publiques et personnelles.
    """
    public = Announcement.objects.filter(is_public=True).order_by('-created_at')[:3]
    personal = Announcement.objects.filter(is_public=False, recipient=request.user).order_by('-created_at')[:3]
    
    return render(request, "announcements/home.html", {
        "public_announcements": public,
        "personal_announcements": personal,
        "title": "Accueil des annonces"
    })


@login_required
def public_announcements(request):
    """
    Liste complète des annonces publiques.
    """
    announcements = Announcement.objects.filter(is_public=True).order_by('-created_at')
    return render(request, "announcements/public_list.html", {
        "announcements": announcements,
        "title": "Annonces publiques"
    })


@login_required
def personal_announcements(request):
    """
    Liste complète des annonces personnelles destinées à l'utilisateur connecté.
    """
    announcements = Announcement.objects.filter(
        is_public=False,
        recipient=request.user
    ).order_by('-created_at')

    return render(request, "announcements/personal_list.html", {
        "announcements": announcements,
        "title": "Vos annonces personnelles"
    })
