# payments/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.conf import settings
from decimal import Decimal
from applications.shop.models import Order, PaymentMessage
from applications.shop.sms_parser import parse_payment_sms
from django.contrib.auth.decorators import login_required
import json
from django.db import IntegrityError
from django.contrib import messages
from applications.portefeuille.models import TransactionPortefeuille
from applications.paiements.models import Depot


@csrf_exempt
def get_post_body(request):
    """
    Supporte application/json ET form-encoded.
    Retourne un dict avec au moins 'message' si possible.
    """
    if request.content_type and "application/json" in request.content_type:
        try:
            data = json.loads(request.body.decode("utf-8"))
            print(data)
        except Exception:
            return {}
    else:
        data = request.POST.dict()
    return data

@csrf_exempt
def sms_webhook(request):

    data = get_post_body(request)
    #sms_text = data.get("message") or data.get("sms") or data.get("body")
    #sender = data.get("from") or data.get("sender") or ""

    sms_text = data.get("message") or data.get("message_content") or data.get("sms") or data.get("body")
    sender = data.get("from") or data.get("sender") or data.get("sender_number") or ""

    if not sms_text:
      return HttpResponseBadRequest("No message provided (aucun message reçu ou conf json)")

    # 2) Sauvegarder le SMS brut (traçabilité)
    msg = PaymentMessage.objects.create(sms_text=sms_text, sender=sender)

    # 3) Extraire montant + référence
    amount, reference = parse_payment_sms(sms_text)
    if not amount or not reference:
        msg.error = "Impossible d'extraire montant/référence"
        msg.save()
        return JsonResponse({"status": "ignored", "reason": "parse_failed"})

    # Remplir et dédupliquer par référence (si le même SMS arrive 2x)
    msg.amount = amount
    msg.reference = reference
    try:
        msg.save()  # échouera si reference déjà prise (unique)
    except Exception:
        # déjà traité avant
        return JsonResponse({"status": "duplicate", "reference": reference})

    # 4) Tenter de valider une commande correspondante
    try:
        order = Order.objects.get(reference_code=reference, is_paid=False)
        # Créer le dépôt
        depot = Depot.objects.create(
                utilisateur=order.user,
                montant=order.amount,
                methode=order.customer_name,
                reference=reference
                        )

                        # Créditer le portefeuille de l'utilisateur
        nouveau_solde = order.user.profil.get_solde() + order.amount
        TransactionPortefeuille.objects.create(
                utilisateur=order.user,
                type='depot',
                montant=order.amount,
                reference=f"{depot.reference}",
                solde_apres=nouveau_solde
                        )
    except Order.DoesNotExist:
        # Pas encore de commande avec ce code -> on garde le SMS en stock
        return JsonResponse({"status": "stored", "reference": reference, "note": "order_not_found_yet"})

    # Vérifier montant strictement égal
    if order.amount == amount:
        order.is_paid = True
        order.save()
        msg.processed = True
        msg.save()
        return JsonResponse({"status": "ok", "message": "Commande validée", "reference": reference})
    else:
        msg.error = f"Montant SMS {amount} != commande {order.amount}"
        msg.save()
        return JsonResponse({"status": "mismatch_amount", "reference": reference})

@login_required
@csrf_exempt
def create_order(request):
    """
    Formulaire minimal pour créer une commande:
    montant + nom client
    """
    if request.method == "POST":
        amount = Decimal(request.POST.get("amount"))
        name = request.POST.get("name") or ""
        order = Order.objects.create(customer_name=name, amount=amount, user=request.user )

        # Stocker l'ID de la commande dans la session pour la récupérer plus tard
        request.session['last_order_id'] = order.id
        return redirect("submit_reference")
        #return render(request, "created.html", {"order": order})

    return render(request, "create.html")

"""@login_required
@csrf_exempt
def submit_reference(request):

    try:
        # Récupérer la commande depuis la session
        order_id = request.session.get('last_order_id')
        if not order_id:
            messages.error(request, "Aucun dépôt trouvé. Veuillez créer une dépôt d'abord.")
            return redirect('create_order')

        order = Order.objects.get(id=order_id)

        if request.method == "POST":
            ref = (request.POST.get("reference_code")).strip()

            if not ref:
                messages.error(request, "Veuillez entrer votre référence de retrait.")
                return render(request, 'submit_reference.html', {"order": order})

            # Vérifier si un message de paiement correspondant existe
            msg = PaymentMessage.objects.filter(reference=ref).order_by("-received_at").first()
            order.reference_code = ref
            order.save()

            if msg:
                #print(f"Montant du message: {msg.amount}, Montant de la commande: {order.amount}")

                if float(msg.amount) == float(order.amount):

                    # Marquer la commande comme payée
                    order.is_paid = True
                    order.save()

                    # Marquer le message comme traité
                    msg.processed = True
                    msg.save()

                    try:
                        # Créer le dépôt
                        depot = Depot.objects.create(
                            utilisateur=request.user,
                            montant=order.amount,
                            methode=order.customer_name,
                            reference=ref
                        )

                        # Créditer le portefeuille de l'utilisateur
                        nouveau_solde = request.user.profil.get_solde() + order.amount
                        TransactionPortefeuille.objects.create(
                            utilisateur=request.user,
                            type='depot',
                            montant=order.amount,
                            reference=f"Dépôt {depot.reference}",
                            solde_apres=nouveau_solde
                        )

                        messages.success(request, "Dépôt effectué avec succès ! Votre compte a été crédité.")
                        return render(request, "paid.html", {
                            "order": order,
                            "note": "Validée immédiatement",
                            "depot": depot
                        })

                    except IntegrityError:
                        messages.error(request, "Une erreur est survenue lors de la création du dépôt. Veuillez réessayer.")
                        return render(request, 'submit_reference_red.html', {"order": order})

                else:
                    messages.error(request, f"Le montant de la référence ({msg.amount}) ne correspond pas au montant de votre commande ({order.amount}).")
                    return render(request, 'submit_reference.html', {"order": order})

            else:
                messages.error(request, "En attente de confirmation du paiement...")
                return render(request, "waiting.html", {"order": order})

        # GET request - afficher le formulaire
        return render(request, "submit_reference.html", {"order": order})

    except Order.DoesNotExist:
        messages.error(request, "Dépôt introuvable, Mettez votre reference reçu par sms.")
        return redirect('create_order')

    except Exception as e:
        messages.error(request, "La ref a été déjà utilisée \n attention votre compte sera bloqué")
        return render(request, 'submit_reference.html')"""


@login_required
def submit_reference(request):
    """
    Le client colle ici son Ref. On rattache ça à la commande via l'ID stocké en session
    """
    try:
        # Récupérer la commande depuis la session
        order_id = request.session.get('last_order_id')
        if not order_id:
            messages.error(request, "Aucun dépôt trouvé. Veuillez créer une dépôt d'abord.")
            return redirect('create_order')

        order = Order.objects.get(id=order_id)

        if request.method == "POST":
            refc = request.POST.get("reference_code", "").strip()
            ref = refc+"."


            # Validation de la référence
            if not ref:
                messages.error(request, "Veuillez entrer votre référence de retrait.")
                return render(request, 'submit_reference.html', {"order": order})

            if len(ref) < 8:  # Ajustez la longueur minimale selon vos besoins
                messages.error(request, "La référence semble trop courte.")
                return render(request, 'submit_reference.html', {"order": order})

            # Vérifier si cette référence a déjà été utilisée
            if Order.objects.filter(reference_code=ref).exclude(id=order.id).exists():
                messages.error(request, "Cette référence a déjà été utilisée.")
                return render(request, 'submit_reference.html', {"order": order})
            order.reference_code = ref
            order.save()

            # Vérifier si un message de paiement correspondant existe
            msg = PaymentMessage.objects.filter(reference=ref).order_by("-received_at").first()
            if not msg:
                msg = PaymentMessage.objects.filter(reference=refc).order_by("-received_at").first()



            if msg:
                print(f"DEBUG - Référence reçue: '{ref}'")
                print(f"DEBUG - Montant message: {msg.amount}, Montant commande: {order.amount}")

                if float(msg.amount) == float(order.amount):

                    order.is_paid =True
                    order.save()

                    # Marquer le message comme traité
                    msg.processed = True
                    msg.save()

                    try:
                        # Créer le dépôt
                        depot = Depot.objects.create(
                            utilisateur=request.user,
                            montant=order.amount,
                            methode=order.customer_name,
                            reference=ref
                        )

                        # Créditer le portefeuille de l'utilisateur
                        nouveau_solde = request.user.profil.get_solde() + order.amount
                        TransactionPortefeuille.objects.create(
                            utilisateur=request.user,
                            type='depot',
                            montant=order.amount,
                            reference=f"{depot.reference}",
                            solde_apres=nouveau_solde
                        )

                        messages.success(request, "Dépôt effectué avec succès ! Votre compte a été crédité.")
                        return render(request, "paid.html", {
                            "order": order,
                            "note": "Validée immédiatement",
                            "depot": depot
                        })

                    except IntegrityError:
                        messages.error(request, "Une erreur est survenue lors de la création du dépôt. Veuillez réessayer.")
                        return render(request, 'submit_reference.html', {"order": order})

                else:
                    messages.error(request, f"Le montant de la référence ({msg.amount}) ne correspond pas au montant de votre commande ({order.amount}).")
                    return render(request, 'submit_reference.html', {"order": order})

            else:
                messages.error(request, "En attente de confirmation du paiement...")
                return render(request, "waiting.html", {"order": order})

        # GET request - afficher le formulaire
        return render(request, "submit_reference.html", {"order": order})

    except Order.DoesNotExist:
        messages.error(request, "Dépôt introuvable. Veuillez créer un nouveau dépôt.")
        return redirect('create_order')

    except Exception as e:
        print(f"ERROR: {str(e)}")  # Debug dans la console
        messages.error(request, f"Une erreur technique est survenue: {str(e)}")
        return render(request, 'submit_reference.html', {"order": order})