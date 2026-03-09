from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Requete, Reponse, PieceJointe
from .forms import RequeteForm, ReponseForm

def index(request):
    """Page d'accueil du service client"""
    return render(request, 'index.html')


def contact(request):
    """Page de contact"""
    return render(request, 'service_client/contact.html')

def login_view(request):
    """Vue de connexion personnalisée pour les clients"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue, {user.username} !')
                return redirect('index')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
        else:
            messages.error(request, 'Veuillez remplir tous les champs.')

    return render(request, 'service_client/login.html')

def logout_view(request):
    """Vue de déconnexion personnalisée"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('index')

class ListeRequetesView(LoginRequiredMixin, ListView):
    """Vue pour lister les requêtes de l'utilisateur connecté"""
    model = Requete
    template_name = 'service_client/liste_requetes.html'
    context_object_name = 'requetes'
    paginate_by = 10

    def get_queryset(self):
        # L'utilisateur ne voit que ses propres requêtes
        return Requete.objects.filter(utilisateur=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuts'] = Requete.STATUT_CHOICES
        return context

class DetailRequeteView(LoginRequiredMixin, DetailView):
    """Vue pour afficher le détail d'une requête"""
    model = Requete
    template_name = 'service_client/detail_requete.html'
    context_object_name = 'requete'

    def get_queryset(self):
        # L'utilisateur ne peut voir que ses propres requêtes
        return Requete.objects.filter(utilisateur=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requete = self.get_object()
        # Récupérer les réponses visibles par le client (non internes)
        context['reponses'] = Reponse.objects.filter(
            requete=requete,
            est_interne=False
        ).order_by('date_creation')
        context['form_reponse'] = ReponseForm()
        return context

class CreerRequeteView(LoginRequiredMixin, CreateView):
    """Vue pour créer une nouvelle requête"""
    model = Requete
    form_class = RequeteForm
    template_name = 'service_client/creer_requete.html'
    success_url = reverse_lazy('liste_requetes')

    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        messages.success(self.request, 'Votre requête a été créée avec succès !')
        return super().form_valid(form)

@login_required
def ajouter_reponse(request, pk):
    """Vue pour ajouter une réponse à une requête"""
    requete = get_object_or_404(Requete, pk=pk, utilisateur=request.user)

    if request.method == 'POST':
        form = ReponseForm(request.POST)
        if form.is_valid():
            reponse = form.save(commit=False)
            reponse.requete = requete
            reponse.auteur = request.user
            reponse.save()
            messages.success(request, 'Votre réponse a été ajoutée avec succès !')
            return redirect('detail_requete', pk=pk)
    else:
        form = ReponseForm()

    return render(request, 'service_client/ajouter_reponse.html', {
        'form': form,
        'requete': requete
    })

@login_required
def recherche_requetes(request):
    """Vue pour rechercher dans les requêtes"""
    query = request.GET.get('q', '')
    statut = request.GET.get('statut', '')

    requetes = Requete.objects.filter(utilisateur=request.user)

    if query:
        requetes = requetes.filter(
            Q(titre__icontains=query) |
            Q(description__icontains=query) |
            Q(categorie__icontains=query)
        )

    if statut:
        requetes = requetes.filter(statut=statut)

    paginator = Paginator(requetes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'service_client/liste_requetes.html', {
        'requetes': page_obj,
        'query': query,
        'statut_selectionne': statut,
        'statuts': Requete.STATUT_CHOICES
    })

# Vues pour l'administration (staff seulement)
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

@method_decorator(staff_member_required, name='dispatch')
class AdminListeRequetesView(ListView):
    """Vue admin pour lister toutes les requêtes"""
    model = Requete
    template_name = 'service_client/admin/liste_requetes.html'
    context_object_name = 'requetes'
    paginate_by = 20

    def get_queryset(self):
        return Requete.objects.all().select_related('utilisateur', 'assigne_a')

@method_decorator(staff_member_required, name='dispatch')
class AdminDetailRequeteView(DetailView):
    """Vue admin pour gérer une requête"""
    model = Requete
    template_name = 'service_client/admin/detail_requete.html'
    context_object_name = 'requete'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requete = self.get_object()
        context['reponses'] = Reponse.objects.filter(requete=requete).order_by('date_creation')
        context['form_reponse'] = ReponseForm()
        return context

@staff_member_required
def admin_ajouter_reponse(request, pk):
    """Vue admin pour ajouter une réponse"""
    requete = get_object_or_404(Requete, pk=pk)

    if request.method == 'POST':
        form = ReponseForm(request.POST)
        if form.is_valid():
            reponse = form.save(commit=False)
            reponse.requete = requete
            reponse.auteur = request.user
            reponse.save()
            messages.success(request, 'Réponse ajoutée avec succès !')
            return redirect('admin_detail_requete', pk=pk)
    else:
        form = ReponseForm()

    return render(request, 'service_client/admin/ajouter_reponse.html', {
        'form': form,
        'requete': requete
    })

@staff_member_required
def admin_changer_statut(request, pk):
    """Vue admin pour changer le statut d'une requête"""
    requete = get_object_or_404(Requete, pk=pk)

    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        if nouveau_statut in [choice[0] for choice in Requete.STATUT_CHOICES]:
            requete.statut = nouveau_statut
            if nouveau_statut == 'traite':
                requete.date_fermeture = timezone.now()
            requete.save()
            messages.success(request, f'Statut changé vers "{requete.get_statut_display()}"')
        return redirect('admin_detail_requete', pk=pk)

    return render(request, 'service_client/admin/changer_statut.html', {
        'requete': requete,
        'statuts': Requete.STATUT_CHOICES
    })
