import json
import csv
import math
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q, Variance
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.core.paginator import Paginator

from .models import Pays, CategorieProduit, Produit, Transaction, ProfilUtilisateur
from .forms import LoginForm, RegisterForm, TransactionForm
from .utils import get_user_role
from functools import wraps


def admin_required(view_func):
    """Décorateur : restreint l'accès aux administrateurs."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if get_user_role(request.user) != 'admin':
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ===================== AUTHENTIFICATION =====================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            ProfilUtilisateur.objects.create(user=user, role='client')
            messages.success(request, "Compte créé avec succès. Connectez-vous.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


# ===================== DASHBOARD =====================

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(statut='valide')

    # Filtre de période
    annee = request.GET.get('annee', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    if annee:
        try:
            annee_int = int(annee)
            transactions = transactions.filter(date_transaction__year=annee_int)
            annee = str(annee_int)  # Garder comme string pour la comparaison dans le template
        except (ValueError, TypeError):
            annee = ''
    if date_debut:
        try:
            transactions = transactions.filter(date_transaction__gte=date_debut)
        except Exception:
            date_debut = ''
    if date_fin:
        try:
            transactions = transactions.filter(date_transaction__lte=date_fin)
        except Exception:
            date_fin = ''

    # Années disponibles pour le filtre
    annees_disponibles = (
        Transaction.objects.filter(statut='valide')
        .dates('date_transaction', 'year')
        .values_list('date_transaction__year', flat=True)
        .distinct()
    )

    total_imports = transactions.filter(type_transaction='importation').aggregate(
        total=Sum('valeur_totale'))['total'] or 0
    total_exports = transactions.filter(type_transaction='exportation').aggregate(
        total=Sum('valeur_totale'))['total'] or 0
    balance = total_exports - total_imports
    nb_transactions = transactions.count()

    # Evolution mensuelle
    evolution_imports = list(
        transactions.filter(type_transaction='importation')
        .annotate(mois=TruncMonth('date_transaction'))
        .values('mois')
        .annotate(total=Sum('valeur_totale'))
        .order_by('mois')
    )
    evolution_exports = list(
        transactions.filter(type_transaction='exportation')
        .annotate(mois=TruncMonth('date_transaction'))
        .values('mois')
        .annotate(total=Sum('valeur_totale'))
        .order_by('mois')
    )

    mois_labels = []
    imports_data = []
    exports_data = []

    all_months = sorted(set(
        [e['mois'] for e in evolution_imports] + [e['mois'] for e in evolution_exports]
    ))
    imports_dict = {e['mois']: float(e['total']) for e in evolution_imports}
    exports_dict = {e['mois']: float(e['total']) for e in evolution_exports}

    for m in all_months:
        mois_labels.append(m.strftime('%b %Y'))
        imports_data.append(imports_dict.get(m, 0))
        exports_data.append(exports_dict.get(m, 0))

    # Top 10 partenaires
    top_partenaires_import = list(
        transactions.filter(type_transaction='importation')
        .values('pays_origine__nom')
        .annotate(total=Sum('valeur_totale'))
        .order_by('-total')[:10]
    )
    top_partenaires_export = list(
        transactions.filter(type_transaction='exportation')
        .values('pays_destination__nom')
        .annotate(total=Sum('valeur_totale'))
        .order_by('-total')[:10]
    )

    # Convertir Decimal en float pour la sérialisation JSON
    for item in top_partenaires_import:
        item['total'] = float(item['total'])
    for item in top_partenaires_export:
        item['total'] = float(item['total'])

    context = {
        'total_imports': total_imports,
        'total_exports': total_exports,
        'balance': balance,
        'nb_transactions': nb_transactions,
        'mois_labels': json.dumps(mois_labels),
        'imports_data': json.dumps(imports_data),
        'exports_data': json.dumps(exports_data),
        'top_partenaires_import': json.dumps(top_partenaires_import),
        'top_partenaires_export': json.dumps(top_partenaires_export),
        'annee': annee,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'annees_disponibles': annees_disponibles,
    }
    return render(request, 'dashboard.html', context)


# ===================== TRANSACTIONS =====================

@login_required
def transactions_list(request):
    transactions = Transaction.objects.select_related('produit', 'pays_origine', 'pays_destination')
    # Les clients ne voient que les transactions validées
    if get_user_role(request.user) != 'admin':
        transactions = transactions.filter(statut='valide')

    type_filtre = request.GET.get('type', '')
    pays_filtre = request.GET.get('pays', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')

    if type_filtre:
        transactions = transactions.filter(type_transaction=type_filtre)
    if pays_filtre:
        transactions = transactions.filter(
            Q(pays_origine__id=pays_filtre) | Q(pays_destination__id=pays_filtre)
        )
    if date_debut:
        try:
            transactions = transactions.filter(date_transaction__gte=date_debut)
        except Exception:
            date_debut = ''
    if date_fin:
        try:
            transactions = transactions.filter(date_transaction__lte=date_fin)
        except Exception:
            date_fin = ''

    pays_list = Pays.objects.all()

    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions': page_obj,
        'pays_list': pays_list,
        'type_filtre': type_filtre,
        'pays_filtre': pays_filtre,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'page_obj': page_obj,
    }
    return render(request, 'transactions.html', context)


# ===================== BALANCE COMMERCIALE =====================

@login_required
def balance_commerciale(request):
    transactions = Transaction.objects.filter(statut='valide')

    # Balance par pays
    pays_imports = dict(
        transactions.filter(type_transaction='importation')
        .values_list('pays_origine__nom')
        .annotate(total=Sum('valeur_totale'))
    )
    pays_exports = dict(
        transactions.filter(type_transaction='exportation')
        .values_list('pays_destination__nom')
        .annotate(total=Sum('valeur_totale'))
    )

    all_pays = sorted(set(list(pays_imports.keys()) + list(pays_exports.keys())))
    balance_par_pays = []
    for pays in all_pays:
        imp = pays_imports.get(pays, Decimal('0'))
        exp = pays_exports.get(pays, Decimal('0'))
        taux_couverture = (exp / imp * 100) if imp > 0 else 0
        balance_par_pays.append({
            'pays': pays,
            'imports': imp,
            'exports': exp,
            'balance': exp - imp,
            'taux_couverture': round(float(taux_couverture), 1),
        })
    balance_par_pays.sort(key=lambda x: x['balance'], reverse=True)

    # Balance par bloc économique
    bloc_imports = dict(
        transactions.filter(type_transaction='importation')
        .values_list('pays_origine__bloc_economique')
        .annotate(total=Sum('valeur_totale'))
    )
    bloc_exports = dict(
        transactions.filter(type_transaction='exportation')
        .values_list('pays_destination__bloc_economique')
        .annotate(total=Sum('valeur_totale'))
    )

    bloc_labels_map = dict(Pays.BLOC_CHOICES)
    all_blocs = sorted(set(list(bloc_imports.keys()) + list(bloc_exports.keys())))
    balance_par_bloc = []
    for bloc in all_blocs:
        imp = bloc_imports.get(bloc, Decimal('0'))
        exp = bloc_exports.get(bloc, Decimal('0'))
        balance_par_bloc.append({
            'bloc': bloc_labels_map.get(bloc, bloc),
            'imports': imp,
            'exports': exp,
            'balance': exp - imp,
        })

    # Données graphique
    graph_pays = [b['pays'] for b in balance_par_pays[:10]]
    graph_imports = [float(b['imports']) for b in balance_par_pays[:10]]
    graph_exports = [float(b['exports']) for b in balance_par_pays[:10]]

    context = {
        'balance_par_pays': balance_par_pays,
        'balance_par_bloc': balance_par_bloc,
        'graph_pays': json.dumps(graph_pays),
        'graph_imports': json.dumps(graph_imports),
        'graph_exports': json.dumps(graph_exports),
    }
    return render(request, 'balance.html', context)


# ===================== ANALYSE PAR PAYS =====================

@admin_required
def analyse_pays(request):
    pays_list = Pays.objects.all()
    pays_id = request.GET.get('pays', '')
    pays_selectionne = None
    top_produits_imp = []
    top_produits_exp = []
    evolution_data = {}

    if pays_id:
        try:
            pays_selectionne = Pays.objects.get(id=pays_id)
            transactions = Transaction.objects.filter(
                statut='valide'
            ).filter(
                Q(pays_origine=pays_selectionne) | Q(pays_destination=pays_selectionne)
            )

            top_produits_imp = list(
                transactions.filter(type_transaction='importation', pays_origine=pays_selectionne)
                .values('produit__nom')
                .annotate(total=Sum('valeur_totale'), qte=Sum('quantite'))
                .order_by('-total')[:10]
            )

            top_produits_exp = list(
                transactions.filter(type_transaction='exportation', pays_destination=pays_selectionne)
                .values('produit__nom')
                .annotate(total=Sum('valeur_totale'), qte=Sum('quantite'))
                .order_by('-total')[:10]
            )

            # Evolution mensuelle avec ce pays
            evo_imp = (
                transactions.filter(type_transaction='importation', pays_origine=pays_selectionne)
                .annotate(mois=TruncMonth('date_transaction'))
                .values('mois')
                .annotate(total=Sum('valeur_totale'))
                .order_by('mois')
            )
            evo_exp = (
                transactions.filter(type_transaction='exportation', pays_destination=pays_selectionne)
                .annotate(mois=TruncMonth('date_transaction'))
                .values('mois')
                .annotate(total=Sum('valeur_totale'))
                .order_by('mois')
            )

            all_months = sorted(set(
                [e['mois'] for e in evo_imp] + [e['mois'] for e in evo_exp]
            ))
            imp_dict = {e['mois']: float(e['total']) for e in evo_imp}
            exp_dict = {e['mois']: float(e['total']) for e in evo_exp}

            evolution_data = {
                'labels': json.dumps([m.strftime('%b %Y') for m in all_months]),
                'imports': json.dumps([imp_dict.get(m, 0) for m in all_months]),
                'exports': json.dumps([exp_dict.get(m, 0) for m in all_months]),
            }

        except Pays.DoesNotExist:
            pass

    context = {
        'pays_list': pays_list,
        'pays_selectionne': pays_selectionne,
        'pays_id': pays_id,
        'top_produits_imp': top_produits_imp,
        'top_produits_exp': top_produits_exp,
        'evolution_data': evolution_data,
    }
    return render(request, 'analyse_pays.html', context)


# ===================== TOP PRODUITS =====================

@login_required
def top_produits(request):
    transactions = Transaction.objects.filter(statut='valide')

    top_importes = list(
        transactions.filter(type_transaction='importation')
        .values('produit__nom', 'produit__categorie__nom')
        .annotate(total_valeur=Sum('valeur_totale'), total_qte=Sum('quantite'))
        .order_by('-total_valeur')[:10]
    )

    top_exportes = list(
        transactions.filter(type_transaction='exportation')
        .values('produit__nom', 'produit__categorie__nom')
        .annotate(total_valeur=Sum('valeur_totale'), total_qte=Sum('quantite'))
        .order_by('-total_valeur')[:10]
    )

    # Répartition par catégorie
    cat_imports = list(
        transactions.filter(type_transaction='importation')
        .values('produit__categorie__nom')
        .annotate(total=Sum('valeur_totale'))
        .order_by('-total')
    )
    cat_exports = list(
        transactions.filter(type_transaction='exportation')
        .values('produit__categorie__nom')
        .annotate(total=Sum('valeur_totale'))
        .order_by('-total')
    )

    context = {
        'top_importes': top_importes,
        'top_exportes': top_exportes,
        'cat_imports_labels': json.dumps([c['produit__categorie__nom'] for c in cat_imports]),
        'cat_imports_data': json.dumps([float(c['total']) for c in cat_imports]),
        'cat_exports_labels': json.dumps([c['produit__categorie__nom'] for c in cat_exports]),
        'cat_exports_data': json.dumps([float(c['total']) for c in cat_exports]),
    }
    return render(request, 'top_produits.html', context)


# ===================== DETECTION ANOMALIES =====================

@admin_required
def detection_anomalies(request):
    transactions = Transaction.objects.filter(statut='valide').select_related(
        'produit', 'pays_origine', 'pays_destination'
    )

    # Calculer les stats par produit pour détecter les anomalies
    stats_produit = (
        transactions.values('produit__id', 'produit__nom')
        .annotate(
            prix_moyen=Avg('prix_unitaire'),
            volume_moyen=Avg('quantite'),
            nb=Count('id'),
        )
    )

    stats_dict = {s['produit__id']: s for s in stats_produit}

    # Calculer l'écart-type manuellement
    variance_data = (
        transactions.values('produit__id')
        .annotate(
            var_prix=Variance('prix_unitaire'),
            var_qte=Variance('quantite'),
        )
    )
    variance_dict = {v['produit__id']: v for v in variance_data}

    # Filtrer uniquement les produits ayant au moins 3 transactions
    produits_valides = [pid for pid, s in stats_dict.items() if s['nb'] >= 3]
    transactions_filtrées = transactions.filter(produit_id__in=produits_valides).iterator(chunk_size=500)

    anomalies = []
    for t in transactions_filtrées:
        stats = stats_dict.get(t.produit_id)
        var = variance_dict.get(t.produit_id)
        if not stats or not var:
            continue

        std_prix = math.sqrt(float(var['var_prix'])) if var['var_prix'] else 0
        std_qte = math.sqrt(float(var['var_qte'])) if var['var_qte'] else 0

        raisons = []
        if std_prix > 0 and abs(float(t.prix_unitaire) - float(stats['prix_moyen'])) > 2 * std_prix:
            raisons.append("Prix anormal")
        if std_qte > 0 and abs(float(t.quantite) - float(stats['volume_moyen'])) > 2 * std_qte:
            raisons.append("Volume anormal")

        if raisons:
            anomalies.append({
                'transaction': t,
                'raisons': ', '.join(raisons),
                'prix_moyen': round(float(stats['prix_moyen']), 2),
                'ecart_prix': round(abs(float(t.prix_unitaire) - float(stats['prix_moyen'])), 2),
            })

    context = {
        'anomalies': anomalies,
        'nb_anomalies': len(anomalies),
        'nb_total': transactions.count(),
    }
    return render(request, 'anomalies.html', context)


# ===================== GRAPHE SANKEY =====================

@admin_required
def sankey_view(request):
    transactions = Transaction.objects.filter(statut='valide')

    type_filtre = request.GET.get('type', '')
    if type_filtre:
        transactions = transactions.filter(type_transaction=type_filtre)

    # Flux par pays origine -> pays destination
    flux = list(
        transactions.values('pays_origine__nom', 'pays_destination__nom')
        .annotate(total=Sum('valeur_totale'))
        .order_by('-total')[:20]
    )

    # Construire les données Sankey
    nodes_set = set()
    for f in flux:
        nodes_set.add(f['pays_origine__nom'])
        nodes_set.add(f['pays_destination__nom'])
    nodes = sorted(nodes_set)
    node_index = {n: i for i, n in enumerate(nodes)}

    sources = []
    targets = []
    values = []
    for f in flux:
        # Éviter les self-loops (origine == destination)
        if f['pays_origine__nom'] == f['pays_destination__nom']:
            continue
        sources.append(node_index[f['pays_origine__nom']])
        targets.append(node_index[f['pays_destination__nom']])
        values.append(float(f['total']))

    context = {
        'nodes': json.dumps(nodes),
        'sources': json.dumps(sources),
        'targets': json.dumps(targets),
        'values': json.dumps(values),
        'type_filtre': type_filtre,
    }
    return render(request, 'sankey.html', context)


# ===================== ANALYSE PAR CODE SH =====================

@admin_required
def analyse_codes_sh(request):
    transactions = Transaction.objects.filter(statut='valide')

    code_filtre = request.GET.get('code', '')

    # Agrégation par catégorie (code SH)
    categories = list(
        transactions.values(
            'produit__categorie__code_sh',
            'produit__categorie__nom'
        )
        .annotate(
            total_imports=Sum('valeur_totale', filter=Q(type_transaction='importation')),
            total_exports=Sum('valeur_totale', filter=Q(type_transaction='exportation')),
            nb_transactions=Count('id'),
        )
        .order_by('produit__categorie__code_sh')
    )

    for cat in categories:
        cat['total_imports'] = cat['total_imports'] or 0
        cat['total_exports'] = cat['total_exports'] or 0
        cat['balance'] = cat['total_exports'] - cat['total_imports']

    # Détails si un code est sélectionné
    detail_produits = []
    categorie_sel = None
    if code_filtre:
        try:
            categorie_sel = CategorieProduit.objects.get(code_sh=code_filtre)
            detail_produits = list(
                transactions.filter(produit__categorie=categorie_sel)
                .values('produit__nom')
                .annotate(
                    total_imports=Sum('valeur_totale', filter=Q(type_transaction='importation')),
                    total_exports=Sum('valeur_totale', filter=Q(type_transaction='exportation')),
                    nb=Count('id'),
                )
                .order_by('-nb')
            )
            for p in detail_produits:
                p['total_imports'] = p['total_imports'] or 0
                p['total_exports'] = p['total_exports'] or 0
        except CategorieProduit.DoesNotExist:
            pass

    # Données graphique
    graph_labels = [c['produit__categorie__code_sh'] + ' - ' + c['produit__categorie__nom'] for c in categories]
    graph_imports = [float(c['total_imports']) for c in categories]
    graph_exports = [float(c['total_exports']) for c in categories]

    context = {
        'categories': categories,
        'code_filtre': code_filtre,
        'categorie_sel': categorie_sel,
        'detail_produits': detail_produits,
        'graph_labels': json.dumps(graph_labels),
        'graph_imports': json.dumps(graph_imports),
        'graph_exports': json.dumps(graph_exports),
    }
    return render(request, 'codes_sh.html', context)


# ===================== ANALYSE PAR BLOC ECONOMIQUE =====================

@admin_required
def analyse_blocs(request):
    transactions = Transaction.objects.filter(statut='valide')
    bloc_labels_map = dict(Pays.BLOC_CHOICES)

    # Imports par bloc
    bloc_imports = dict(
        transactions.filter(type_transaction='importation')
        .values_list('pays_origine__bloc_economique')
        .annotate(total=Sum('valeur_totale'))
    )
    bloc_exports = dict(
        transactions.filter(type_transaction='exportation')
        .values_list('pays_destination__bloc_economique')
        .annotate(total=Sum('valeur_totale'))
    )

    # Nb transactions par bloc
    bloc_nb_imp = dict(
        transactions.filter(type_transaction='importation')
        .values_list('pays_origine__bloc_economique')
        .annotate(nb=Count('id'))
    )
    bloc_nb_exp = dict(
        transactions.filter(type_transaction='exportation')
        .values_list('pays_destination__bloc_economique')
        .annotate(nb=Count('id'))
    )

    all_blocs = sorted(set(list(bloc_imports.keys()) + list(bloc_exports.keys())))
    blocs_data = []
    for bloc in all_blocs:
        imp = bloc_imports.get(bloc, Decimal('0'))
        exp = bloc_exports.get(bloc, Decimal('0'))
        taux = (exp / imp * 100) if imp > 0 else 0
        blocs_data.append({
            'code': bloc,
            'nom': bloc_labels_map.get(bloc, bloc),
            'imports': imp,
            'exports': exp,
            'balance': exp - imp,
            'taux_couverture': round(float(taux), 1),
            'nb_imports': bloc_nb_imp.get(bloc, 0),
            'nb_exports': bloc_nb_exp.get(bloc, 0),
        })

    # Top pays par bloc sélectionné
    bloc_filtre = request.GET.get('bloc', '')
    pays_du_bloc = []
    if bloc_filtre:
        pays_imp = dict(
            transactions.filter(type_transaction='importation', pays_origine__bloc_economique=bloc_filtre)
            .values_list('pays_origine__nom')
            .annotate(total=Sum('valeur_totale'))
        )
        pays_exp = dict(
            transactions.filter(type_transaction='exportation', pays_destination__bloc_economique=bloc_filtre)
            .values_list('pays_destination__nom')
            .annotate(total=Sum('valeur_totale'))
        )
        all_pays = sorted(set(list(pays_imp.keys()) + list(pays_exp.keys())))
        for pays in all_pays:
            pays_du_bloc.append({
                'nom': pays,
                'imports': pays_imp.get(pays, Decimal('0')),
                'exports': pays_exp.get(pays, Decimal('0')),
            })

    # Données graphiques
    graph_labels = [b['nom'] for b in blocs_data]
    graph_imports = [float(b['imports']) for b in blocs_data]
    graph_exports = [float(b['exports']) for b in blocs_data]

    context = {
        'blocs_data': blocs_data,
        'bloc_filtre': bloc_filtre,
        'bloc_filtre_nom': bloc_labels_map.get(bloc_filtre, bloc_filtre),
        'pays_du_bloc': pays_du_bloc,
        'graph_labels': json.dumps(graph_labels),
        'graph_imports': json.dumps(graph_imports),
        'graph_exports': json.dumps(graph_exports),
    }
    return render(request, 'blocs.html', context)


# ===================== EXPORT CSV =====================

@admin_required
def export_csv(request):
    type_export = request.GET.get('type', 'transactions')
    transactions = Transaction.objects.filter(statut='valide').select_related(
        'produit', 'produit__categorie', 'pays_origine', 'pays_destination'
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="export_{type_export}.csv"'
    response.write('\ufeff')  # BOM pour Excel
    writer = csv.writer(response, delimiter=';')

    if type_export == 'transactions':
        writer.writerow(['N° Déclaration', 'Type', 'Produit', 'Catégorie', 'Code SH',
                         'Origine', 'Destination', 'Quantité', 'Prix Unitaire',
                         'Valeur Totale', 'Date', 'Transport', 'Statut'])
        for t in transactions:
            writer.writerow([
                t.numero_declaration, t.get_type_transaction_display(),
                t.produit.nom, t.produit.categorie.nom, t.produit.categorie.code_sh,
                t.pays_origine.nom, t.pays_destination.nom,
                t.quantite, t.prix_unitaire, t.valeur_totale,
                t.date_transaction.strftime('%d/%m/%Y'),
                t.get_mode_transport_display(), t.get_statut_display()
            ])

    elif type_export == 'balance':
        writer.writerow(['Pays', 'Importations', 'Exportations', 'Balance', 'Taux de Couverture (%)'])
        pays_imports = dict(
            transactions.filter(type_transaction='importation')
            .values_list('pays_origine__nom').annotate(total=Sum('valeur_totale'))
        )
        pays_exports = dict(
            transactions.filter(type_transaction='exportation')
            .values_list('pays_destination__nom').annotate(total=Sum('valeur_totale'))
        )
        all_pays = sorted(set(list(pays_imports.keys()) + list(pays_exports.keys())))
        for pays in all_pays:
            imp = pays_imports.get(pays, 0)
            exp = pays_exports.get(pays, 0)
            taux = round(float(exp / imp * 100), 1) if imp > 0 else 0
            writer.writerow([pays, imp, exp, exp - imp, taux])

    elif type_export == 'produits':
        writer.writerow(['Produit', 'Catégorie', 'Code SH', 'Total Importations', 'Total Exportations', 'Nb Transactions'])
        produits = (
            transactions.values('produit__nom', 'produit__categorie__nom', 'produit__categorie__code_sh')
            .annotate(
                total_imp=Sum('valeur_totale', filter=Q(type_transaction='importation')),
                total_exp=Sum('valeur_totale', filter=Q(type_transaction='exportation')),
                nb=Count('id'),
            ).order_by('-nb')
        )
        for p in produits:
            writer.writerow([
                p['produit__nom'], p['produit__categorie__nom'], p['produit__categorie__code_sh'],
                p['total_imp'] or 0, p['total_exp'] or 0, p['nb']
            ])

    return response


# ===================== SERIES TEMPORELLES AVANCEES =====================

@admin_required
def series_temporelles(request):
    transactions = Transaction.objects.filter(statut='valide')

    # Evolution mensuelle détaillée
    evolution_imports = list(
        transactions.filter(type_transaction='importation')
        .annotate(mois=TruncMonth('date_transaction'))
        .values('mois')
        .annotate(total=Sum('valeur_totale'), nb=Count('id'))
        .order_by('mois')
    )
    evolution_exports = list(
        transactions.filter(type_transaction='exportation')
        .annotate(mois=TruncMonth('date_transaction'))
        .values('mois')
        .annotate(total=Sum('valeur_totale'), nb=Count('id'))
        .order_by('mois')
    )

    all_months = sorted(set(
        [e['mois'] for e in evolution_imports] + [e['mois'] for e in evolution_exports]
    ))
    imp_dict = {e['mois']: float(e['total']) for e in evolution_imports}
    exp_dict = {e['mois']: float(e['total']) for e in evolution_exports}

    labels = [m.strftime('%b %Y') for m in all_months]
    imports_data = [imp_dict.get(m, 0) for m in all_months]
    exports_data = [exp_dict.get(m, 0) for m in all_months]

    # Moyennes mobiles (fenêtre de 3 mois)
    def moving_average(data, window=3):
        result = []
        for i in range(len(data)):
            start = max(0, i - window + 1)
            result.append(round(sum(data[start:i+1]) / (i - start + 1), 2))
        return result

    mm_imports = moving_average(imports_data)
    mm_exports = moving_average(exports_data)

    # Variation mensuelle (%)
    var_imports = [0]
    var_exports = [0]
    for i in range(1, len(imports_data)):
        vi = round(((imports_data[i] - imports_data[i-1]) / imports_data[i-1] * 100), 1) if imports_data[i-1] else 0
        ve = round(((exports_data[i] - exports_data[i-1]) / exports_data[i-1] * 100), 1) if exports_data[i-1] else 0
        var_imports.append(vi)
        var_exports.append(ve)

    # Balance mensuelle
    balance_data = [exports_data[i] - imports_data[i] for i in range(len(all_months))]

    context = {
        'labels': json.dumps(labels),
        'imports_data': json.dumps(imports_data),
        'exports_data': json.dumps(exports_data),
        'mm_imports': json.dumps(mm_imports),
        'mm_exports': json.dumps(mm_exports),
        'var_imports': json.dumps(var_imports),
        'var_exports': json.dumps(var_exports),
        'balance_data': json.dumps(balance_data),
    }
    return render(request, 'series_temporelles.html', context)


# ===================== CRUD TRANSACTIONS =====================

@admin_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction créée avec succès.")
            return redirect('transactions')
    else:
        form = TransactionForm()
    return render(request, 'transaction_form.html', {'form': form, 'titre': 'Nouvelle Transaction'})


@admin_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction modifiée avec succès.")
            return redirect('transactions')
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'transaction_form.html', {'form': form, 'titre': 'Modifier Transaction', 'transaction': transaction})


@admin_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, "Transaction supprimée.")
        return redirect('transactions')
    return render(request, 'transaction_confirm_delete.html', {'transaction': transaction})
