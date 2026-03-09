# personnel/test_signals.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import Personnel, ObjectifPersonnel, PostulerObjectif, PerformancePersonnel
from applications.produits.models import Produit, Achat
from applications.portefeuille.models import BonusParrainage

User = get_user_model()

def test_signal_integration():
    """Test complet du flux des signaux"""
    print("🧪 Début du test des signaux...")
    
    # 1. Créer les utilisateurs
    print("1. Création des utilisateurs...")
    parrain_user = User.objects.create_user(
        email="parrain@test.com",
        password="test123",
        first_name="Parrain",
        last_name="Test"
    )
    
    filleul_user = User.objects.create_user(
        email="filleul@test.com", 
        password="test123",
        first_name="Filleul",
        last_name="Test"
    )
    
    # 2. Créer le profil Personnel pour le parrain
    print("2. Création du profil Personnel...")
    personnel = Personnel.objects.create(
        utilisateur=parrain_user,
        poste="Testeur"
    )
    print(f"   ✅ Personnel créé: {personnel}")
    
    # 3. Créer un produit
    print("3. Création du produit...")
    produit = Produit.objects.create(
        nom="Produit Test",
        description="Produit pour test",
        prix=Decimal('100.00'),
        duree_jours=30
    )
    print(f"   ✅ Produit créé: {produit}")
    
    # 4. Créer un objectif
    print("4. Création de l'objectif...")
    objectif = ObjectifPersonnel.objects.create(
        intitule="Objectif Test",
        date_debut=date.today(),
        date_fin=date.today() + timedelta(days=30),
        nombre_filleuls_requis=1,
        prime_objectif=Decimal('50.00')
    )
    objectif.produits_eligibles.add(produit)
    print(f"   ✅ Objectif créé: {objectif}")
    
    # 5. Postuler à l'objectif
    print("5. Postulation à l'objectif...")
    postulation = PostulerObjectif.objects.create(
        personnel=personnel,
        objectif=objectif,
        statut='en_attente'
    )
    print(f"   ✅ Postulation créée: {postulation}")
    
    # 6. Accepter la postulation (devrait déclencher le signal)
    print("6. Acceptation de la postulation...")
    postulation.statut = 'accepte'
    postulation.save()
    print(f"   ✅ Postulation acceptée")
    
    # Vérifier si la performance a été créée
    try:
        performance = postulation.performance
        print(f"   ✅ Performance créée: {performance}")
    except Exception as e:
        print(f"   ❌ Performance NON créée: {e}")
        return False
    
    # 7. Créer la relation de parrainage
    print("7. Création relation parrainage...")
    bonus_parrainage = BonusParrainage.objects.create(
        parrain=parrain_user,
        filleul=filleul_user,
        achat=None,  # Temporairement null pour le test
        montant=Decimal('10.00'),
        pourcentage=Decimal('10.00')
    )
    print(f"   ✅ Relation parrainage créée: {bonus_parrainage}")
    
    # 8. Créer un achat du filleul (devrait déclencher le signal)
    print("8. Création achat du filleul...")
    achat = Achat.objects.create(
        utilisateur=filleul_user,
        produit=produit,
        prix_au_moment_achat=produit.prix,
        date_fin=date.today() + timedelta(days=30)
    )
    print(f"   ✅ Achat créé: {achat}")
    
    # Mettre à jour le bonus parrainage avec l'achat
    bonus_parrainage.achat = achat
    bonus_parrainage.save()
    
    # 9. Vérifier si le filleul a été détecté
    print("9. Vérification détection filleul...")
    performance.refresh_from_db()
    filleuls_count = performance.filleuls.count()
    print(f"   📊 Filleuls détectés: {filleuls_count}")
    
    if filleuls_count > 0:
        filleul = performance.filleuls.first()
        print(f"   ✅ Filleul détecté: {filleul} - Éligible: {filleul.est_eligible}")
    else:
        print("   ❌ Aucun filleul détecté")
        return False
    
    # 10. Vérifier si l'objectif est atteint
    print("10. Vérification objectif atteint...")
    performance.refresh_from_db()
    print(f"   📊 Statut performance: {performance.statut}")
    print(f"   📊 Filleuls qualifiés: {performance.nombre_filleuls_qualifies}/{objectif.nombre_filleuls_requis}")
    
    if performance.statut == 'atteint':
        print("   ✅ Objectif atteint!")
        
        # Vérifier si la prime a été versée
        if performance.prime_recue:
            print("   ✅ Prime versée!")
        else:
            print("   ⚠️ Prime non versée")
    else:
        print("   ❌ Objectif non atteint")
    
    print("🎉 Test terminé!")
    return True

if __name__ == "__main__":
    test_signal_integration()

