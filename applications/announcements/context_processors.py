from .models import Announcement

# Contexte global pour les annonces dans l'en-tête
def announcements_context(request):
    if request.user.is_authenticated:
        public_announcements = Announcement.objects.filter(is_public=True).order_by('-created_at')[:5]
        personal_announcements = Announcement.objects.filter(
            is_public=False,
            recipient=request.user
        ).order_by('-created_at')[:5]

        return {
            'public_announcements': public_announcements,
            'personal_announcements': personal_announcements,
            'public_announcements_count': public_announcements.count(),
            'personal_announcements_count': personal_announcements.count(),
        }
    return {}
