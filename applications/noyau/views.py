from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from applications.portefeuille.models import TransactionPortefeuille, CapitalClient
from applications.produits.models import Achat
from applications.paiements.models import Depot
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Q
from django.db.models import DecimalField
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import Coalesce
import uuid
from django.http import FileResponse
import os
from django.conf import settings

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

import json
from applications.comptes.models import ProfilUtilisateur

def vue_accueil(request):
    """Vue pour la page d'accueil."""
    return render(request, 'noyau/accueil.html')

def vue_offline(request):
    """Vue pour la page hors ligne."""
    return render(request, 'noyau/offline.html')

def favicon_view(request):
    """Vue pour servir le favicon.ico."""
    from django.http import HttpResponse, Http404
    from django.conf import settings
    import os
    
    # Chercher le fichier favicon ou utiliser l'icône Genius Africa
    favicon_path = None
    
    # D'abord chercher favicon.ico dans static
    if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        favicon_path = os.path.join(settings.STATIC_ROOT, 'image', 'Genius_Africa.png')
        if not os.path.exists(favicon_path):
            favicon_path = None
    
    if not favicon_path and hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        for static_dir in settings.STATICFILES_DIRS:
            potential_path = os.path.join(static_dir, 'image', 'Genius_Africa.png')
            if os.path.exists(potential_path):
                favicon_path = potential_path
                break
    
    if favicon_path and os.path.exists(favicon_path):
        try:
            from django.http import FileResponse
            return FileResponse(open(favicon_path, 'rb'), content_type='image/png')
        except Exception as e:
            return HttpResponse(f"Erreur: {str(e)}", status=500)
    
    # Si aucun fichier n'est trouvé, retourner 404
    return HttpResponse("Favicon non trouvé", status=404)

def manifest_json(request):
    """Vue pour servir le manifest.json avec les bons headers."""
    from django.http import HttpResponse
    from django.conf import settings
    import os
    import json
    
    # Chercher le fichier dans STATIC_ROOT ou STATICFILES_DIRS
    manifest_path = None
    
    # D'abord chercher dans STATIC_ROOT (production)
    if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        manifest_path = os.path.join(settings.STATIC_ROOT, 'manifest.json')
        if not os.path.exists(manifest_path):
            manifest_path = None
    
    # Sinon chercher dans STATICFILES_DIRS (développement)
    if not manifest_path and hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        for static_dir in settings.STATICFILES_DIRS:
            potential_path = os.path.join(static_dir, 'manifest.json')
            if os.path.exists(potential_path):
                manifest_path = potential_path
                break
    
    if manifest_path and os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Valider que c'est du JSON valide
                json.loads(content)
        except json.JSONDecodeError as e:
            return HttpResponse(
                json.dumps({"error": "Manifest JSON invalide"}),
                content_type='application/json',
                status=500
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({"error": f"Erreur lors du chargement: {str(e)}"}),
                content_type='application/json',
                status=500
            )
    else:
        return HttpResponse(
            json.dumps({"error": "Manifest non trouvé"}),
            content_type='application/json',
            status=404
        )
    
    # Créer la réponse avec les bons headers
    response = HttpResponse(content, content_type='application/manifest+json')
    response['Cache-Control'] = 'public, max-age=3600'  # Cache pendant 1 heure
    response['X-Content-Type-Options'] = 'nosniff'
    
    return response

def service_worker(request):
    """Vue pour servir le service worker avec les bons headers."""
    from django.http import HttpResponse, Http404
    from django.conf import settings
    import os
    
    # Chercher le fichier dans STATIC_ROOT ou STATICFILES_DIRS
    sw_path = None
    
    # D'abord chercher dans STATIC_ROOT (production)
    if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        sw_path = os.path.join(settings.STATIC_ROOT, 'js', 'service-worker.js')
        if not os.path.exists(sw_path):
            sw_path = None
    
    # Sinon chercher dans STATICFILES_DIRS (développement)
    if not sw_path and hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        for static_dir in settings.STATICFILES_DIRS:
            potential_path = os.path.join(static_dir, 'js', 'service-worker.js')
            if os.path.exists(potential_path):
                sw_path = potential_path
                break
    
    if sw_path and os.path.exists(sw_path):
        try:
            with open(sw_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            # En cas d'erreur de lecture, retourner une erreur 500
            return HttpResponse(
                f"// Erreur lors du chargement du Service Worker: {str(e)}",
                content_type='application/javascript',
                status=500
            )
    else:
        # Si le fichier n'existe pas, retourner 404
        return HttpResponse(
            "// Service Worker - Fichier non trouvé",
            content_type='application/javascript',
            status=404
        )
    
    # Créer la réponse avec les bons headers
    response = HttpResponse(content, content_type='application/javascript')
    
    # Headers essentiels pour le Service Worker
    response['Service-Worker-Allowed'] = '/'  # Permet au SW de contrôler toute l'application
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # Ne jamais mettre en cache
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Content-Type-Options'] = 'nosniff'
    
    return response

@login_required(login_url='accueil')
def vue_tableau_de_bord(request):
        #capital, created = CapitalClient.objects.get_or_create(utilisateur=request.user )

        if request.user.is_authenticated:
            try:
                    """Vue pour le tableau de bord utilisateur avec données dynamiques."""
                    from django.db.utils import OperationalError

                    try:
                        capital = CapitalClient.objects.filter(utilisateur=request.user).first()
                        if capital:
                            solde_capital = capital.capital
                        else:
                            solde_capital = 0
                    except OperationalError:
                        # La table n'existe pas encore
                        solde_capital = 0
                    # Récupérer les transactions récentes
                    transactions = TransactionPortefeuille.objects.filter(utilisateur=request.user).order_by('-cree_le')
                    solde = request.user.profil.get_solde()
                    solde_et_solde_capital = float(solde + solde_capital)
                    # capital que l'utilisateur a investit
                    capital_actifs = Achat.objects.filter(
                        utilisateur=request.user,
                        statut='actif',
                        est_reinvesti=False,
                    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

                    # partie pour gerer les trader inactif et non reinvest

                    today = timezone.now().date()
                    # Filtrer les achats expirés et non réinvestis
                    achats = Achat.objects.filter(
                        utilisateur=request.user,
                        est_reinvesti=False
                    ).filter(
                        Q(statut="expire") | Q(date_fin__lt=today)
                    )
                    # Calculer la somme
                    total_trader_inactif = achats.aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

                    # dasn le cas ou les deus ont de valeur
                    totaux_gen =  total_trader_inactif + capital_actifs
                    # Calculer le solde (exemple simplifié)
                    #solde = sum(t.montant for t in TransactionPortefeuille.objects.filter(utilisateur=request.user, type__in=['depot', 'gain_quotidien', 'bonus_parrainage'])) - sum(t.montant for t in TransactionPortefeuille.objects.filter(utilisateur=request.user, type='retrait'))

                    # Calculer les gains d'aujourd'hui
                    gains_aujourdhui = sum(t.montant for t in TransactionPortefeuille.objects.filter(utilisateur=request.user, type='gain_quotidien', cree_le__date=timezone.now().date()))

                    # Calculer le total des dépôts
                    total_depots = sum(d.montant for d in Depot.objects.filter(utilisateur=request.user, statut='confirme'))

                    # Récupérer les achats actifs
                    achats_actifs = Achat.objects.filter(utilisateur=request.user, statut='actif')

                    return render(request, 'noyau/tableau_de_bord.html', {
                        'transactions': transactions,
                        'solde': solde,
                        'solde_et_solde_capital':solde_et_solde_capital,
                        'gains_aujourdhui': gains_aujourdhui,
                        'total_depots': total_depots,
                        'achats_actifs': achats_actifs,
                        'capital_actifs':capital_actifs,
                        'achats' : achats,
                        'total_trader_inactif':  total_trader_inactif,
                        'totaux_gen': totaux_gen # gerant tous


                    })



            except ProfilUtilisateur.DoesNotExist:
                messages.error(request, "Votre profil n'existe pas. Il va être créé.")
                ProfilUtilisateur.objects.create(utilisateur=request.user)
                solde = 0

            return render(request, 'noyau/tableau_de_bord.html', {'solde': solde})
        else:
             return redirect('accueil')




@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def vue_connexion(request):
    """Vue pour la connexion des utilisateurs avec protection CSRF renforcée."""
    if request.method == 'POST':
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')
        
        if not email or not mot_de_passe:
            messages.error(request, "Veuillez remplir tous les champs.")
            response = render(request, 'noyau/connexion.html')
        else:
            utilisateur = authenticate(request, username=email, password=mot_de_passe)

            if utilisateur is not None:
                login(request, utilisateur)
                # Redirection après connexion réussie
                return redirect('tableau_de_bord')
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
                response = render(request, 'noyau/connexion.html')
        
        # Headers pour éviter le cache sur toutes les réponses POST
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        response['X-Frame-Options'] = 'DENY'
        return response
    
    # GET request - afficher le formulaire avec headers anti-cache
    response = render(request, 'noyau/connexion.html')
    # Headers pour éviter le cache sur la page de connexion (très stricts)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Frame-Options'] = 'DENY'
    response['Vary'] = '*'  # Empêcher la mise en cache par les proxies
    # Ajouter un timestamp pour forcer le rechargement
    import time
    response['Last-Modified'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
    return response
    # Headers pour éviter le cache de la page de connexion
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    
    return response

def vue_deconnexion(request):
    """Vue pour la déconnexion."""
    logout(request)
    return redirect('accueil')







@login_required
def tableau_capital(request):
    # Capital des produits ACTIFS
    capital_actifs = Achat.objects.filter(
        utilisateur=request.user,
        statut='actif',
        date_fin__gte=timezone.now().date()  # Vérifie aussi la date
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

    # Capital des produits EXPIRÉS
    capital_expires = Achat.objects.filter(
        utilisateur=request.user,
        statut='expire'
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

    # Capital des produits ANNULÉS
    capital_annules = Achat.objects.filter(
        utilisateur=request.user,
        statut='annule'
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

    # Capital TOTAL (tous statuts)
    capital_total = Achat.objects.filter(
        utilisateur=request.user
    ).aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0

    context = {
        'capital_actifs': capital_actifs,
        'capital_expires': capital_expires,
        'capital_annules': capital_annules,
        'capital_total': capital_total,
    }

    return render(request, 'noyau/capital.html', context)





@login_required
def get_achats_expirés_non_reinvestis(request):
    today = timezone.now().date()
    #reference = str(uuid.uuid4())
    # Filtrer les achats expirés et non réinvestis
    achats = Achat.objects.filter(
        utilisateur=request.user,
        est_reinvesti=False
    ).filter(
        Q(statut="expire") | Q(date_fin__lt=today)
    )

    # Calculer la somme
    total = achats.aggregate(total=Sum('prix_au_moment_achat'))['total'] or 0
    context = {'achats' : achats, 'total':  total}
    print(total)
    try:
            if total != 0:

                            # partie traiter capital
                control_capital, created = CapitalClient.objects.get_or_create(utilisateur=request.user )
                if control_capital:
                            control_capital.capital += total  # On incrémente correctement
                            control_capital.save()            # On enregistre la modification

                achats.update(est_reinvesti=True)
                return redirect('tableau_de_bord')
            else:
                 return redirect('tableau_de_bord')
    except:
         return render(request, 'noyau/tableau_de_bord.html', context)



def faq(request):
     return render(request, 'noyau/faq.html')

def condition_utilisation(request):
     return render(request, 'noyau/condition.html')

def politique_confid(request):
     return render(request, 'noyau/politique_con.html')

def comment_faire_un_depot(request):
     return render(request, 'noyau/comment_faire_depot.html')


# dans views.py
from django.shortcuts import render

def custom_404(request, exception):
    return render(request, "404.html", status=404)


def admin_fonction(request):
     return redirect('admin')

def resilier_contrat(request):
    return render(request, 'resilier.html')




def download_app(request):
    # Chemin complet vers ton fichier
    filepath = os.path.join(settings.BASE_DIR, "apps_genius", "Genius_africa.apk")

    # Ouvrir le fichier et le renvoyer en téléchargement
    return FileResponse(open(filepath, "rb"), as_attachment=True, filename="Genius_africa.apk")








##################################################################################
##################################################################################


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from applications.announcements.models import Announcement



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from applications.announcements.models import Announcement

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




