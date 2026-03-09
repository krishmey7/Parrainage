# personnel/views.py
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from datetime import date
from .models import (
    ObjectifPersonnel, PostulerObjectif,
    PerformancePersonnel, PrimePersonnel, FilleulPersonnel
)



# personnel/utils.py
from decimal import Decimal
from datetime import date
from .models import Personnel

def get_or_create_personnel(user):
    """
    Retourne le profil Personnel pour un utilisateur.
    Crée automatiquement le profil s'il n'existe pas.
    """
    try:
        return user.personnel
    except Personnel.DoesNotExist:
        # Création automatique
        personnel = Personnel.objects.create(
            utilisateur=user,
            poste='Journalier',
            date_embauche=date.today(),
            salaire_base=Decimal('0.00')
        )
        return personnel

def est_personnel(user):
    """Vérifie si l'utilisateur fait partie du personnel"""
    return hasattr(user, 'personnel')
# personnel/views.py
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from datetime import date
from .models import (
    ObjectifPersonnel, PostulerObjectif,
    PerformancePersonnel, PrimePersonnel, FilleulPersonnel
)



# personnel/utils.py
from decimal import Decimal
from datetime import date
from .models import Personnel

def get_or_create_personnel(user):
    """
    Retourne le profil Personnel pour un utilisateur.
    Crée automatiquement le profil s'il n'existe pas.
    """
    try:
        return user.personnel
    except Personnel.DoesNotExist:
        # Création automatique
        personnel = Personnel.objects.create(
            utilisateur=user,
            poste='Collaborateur',
            date_embauche=date.today(),
            salaire_base=Decimal('0.00')
        )
        return personnel











@login_required
def tableau_de_bord_personnel(request):
    """Tableau de bord du personnel connecté"""

    personnel = get_or_create_personnel(request.user)

    # Postulations acceptées avec performances
    postulations_acceptees = PostulerObjectif.objects.filter(
        personnel=personnel,
        statut="accepte"
    ).select_related('objectif', 'performance')

    objectifs_actifs = []
    for postulation in postulations_acceptees:
        progression = 0
        if hasattr(postulation, 'performance') and postulation.performance:
            progression = postulation.performance.progression_pourcentage

        obj_data = {
            'objectif': postulation.objectif,
            'postulation': postulation,
            'performance': getattr(postulation, 'performance', None),
            'progression': progression,
        }
        objectifs_actifs.append(obj_data)

    # Statistiques mensuelles avec valeurs par défaut
    aujourd_hui = timezone.now().date()
    debut_mois = aujourd_hui.replace(day=1)

    stats = PerformancePersonnel.objects.filter(
        postulation__personnel=personnel,
        postulation__objectif__date_debut__gte=debut_mois,
        statut='atteint'
    ).aggregate(
        total_filleuls=Sum('nombre_filleuls_qualifies'),
        total_primes=Sum('postulation__objectif__prime_objectif')
    )
    #print(stats)

    # Assurer que les valeurs ne sont pas None
    stats_mensuelles = {
        'total_filleuls': stats['total_filleuls'] or 0,
        'total_primes': stats['total_primes'] or Decimal('0.00')
    }

    # Primes récentes
    primes_recentes = PrimePersonnel.objects.filter(
        personnel=personnel
    ).select_related('objectif').order_by('-date_versement')[:5]

    context = {
        'personnel': personnel,
        'stats_mensuelles': stats_mensuelles,
        'objectifs_actifs': objectifs_actifs,
        'primes_recentes': primes_recentes,
    }

    return render(request, 'personnel/tableau_de_bord.html', context)


@login_required
@user_passes_test(est_personnel)
def detail_objectif(request, objectif_id):
    """Détail d'un objectif spécifique avec progression et ses filleuls"""

    personnel = get_or_create_personnel(request.user)

    postulation = get_object_or_404(
        PostulerObjectif.objects.select_related("objectif", "performance"),
        objectif_id=objectif_id,
        personnel=personnel
    )

    objectif = postulation.objectif
    performance = getattr(postulation, "performance", None)

    # Récupération des filleuls si performance existe
    filleuls = []
    if performance:
        filleuls = FilleulPersonnel.objects.filter(
            performance=performance
        ).select_related('filleul', 'produit_achete', 'achat_filleul')

    context = {
        "objectif": objectif,
        "postulation": postulation,
        "performance": performance,
        "filleuls": filleuls,
    }

    return render(request, "personnel/detail_objectif.html", context)

@login_required
@user_passes_test(est_personnel)
def historique_primes(request):
    """Historique complet des primes du personnel avec totaux"""

    personnel = get_or_create_personnel(request.user)

    primes = (
        PrimePersonnel.objects.filter(personnel=personnel)
        .select_related("objectif")
        .order_by("-date_versement")
    )

    total_primes = primes.aggregate(total=Sum("montant_prime"))["total"] or 0

    context = {
        "primes": primes,
        "total_primes": total_primes,
    }

    return render(request, "personnel/historique_primes.html", context)

@login_required
def liste_objectifs(request):
    """Affiche tous les objectifs et permet au personnel de postuler"""

    personnel = get_or_create_personnel(request.user)

    # POST = Le personnel postule à un objectif
    if request.method == "POST":
        objectif_id = request.POST.get("objectif_id")

        if not objectif_id:
            messages.error(request, "Aucun objectif sélectionné.")
            return redirect('personnel:liste_objectifs')

        try:
            objectif = ObjectifPersonnel.objects.get(id=objectif_id, est_actif=True)
        except ObjectifPersonnel.DoesNotExist:
            messages.error(request, "L'objectif sélectionné n'existe pas ou n'est plus actif.")
            return redirect('personnel:liste_objectifs')

        # Vérifications supplémentaires
        if not objectif.est_en_cours:
            messages.warning(request, "Cet objectif n'est plus en cours.")
            return redirect('personnel:liste_objectifs')

        # Vérifier si le personnel a déjà postulé
        deja_postule = PostulerObjectif.objects.filter(
            personnel=personnel,
            objectif=objectif
        ).exists()

        if deja_postule:
            messages.info(request, "Vous avez déjà postulé à cet objectif.")
            return redirect('personnel:tableau_de_bord')

        # Création de la postulation
        postulation = PostulerObjectif.objects.create(
            personnel=personnel,
            objectif=objectif
        )

        # Création automatique de la performance liée à la postulation
        #PerformancePersonnel.objects.create( postulation=postulation)

        messages.success(request, "Votre candidature a été enregistrée avec succès et est en attente de validation.")
        return redirect('personnel:tableau_de_bord')

    # Récupération de tous les objectifs actifs et en cours
    """objectifs = ObjectifPersonnel.objects.filter(
        est_actif=True
    ).prefetch_related('postulations').order_by('-date_creation')"""


    objectifs = ObjectifPersonnel.objects.filter( est_actif=True).prefetch_related('produits_eligibles', 'postulations').order_by('-date_creation')

    # Liste des objectifs auxquels l'utilisateur a déjà postulé
    objectifs_postules = PostulerObjectif.objects.filter(
        personnel=personnel
    ).values_list('objectif_id', flat=True)

    return render(request, 'personnel/postuler.html', {
        'objectifs': objectifs,
        'objectifs_postules': objectifs_postules,
        'personnel': personnel,
    })

@login_required
@user_passes_test(est_personnel)
def mes_postulations(request):
    """Affiche toutes les postulations du personnel"""

    personnel = get_or_create_personnel(request.user)

    postulations = PostulerObjectif.objects.filter(
        personnel=personnel
    ).select_related('objectif', 'performance').order_by('-date_postulation')

    context = {
        'postulations': postulations,
    }

    return render(request, 'personnel/mes_postulations.html', context)