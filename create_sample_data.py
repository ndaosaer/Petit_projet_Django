import os
import sys
import django
import random
from decimal import Decimal
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'suivi_import_export.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from commerce.models import Pays, CategorieProduit, Produit, Transaction

print("Suppression des anciennes données...")
Transaction.objects.all().delete()
Produit.objects.all().delete()
CategorieProduit.objects.all().delete()
Pays.objects.all().delete()

# ===================== PAYS =====================
print("Création des pays...")
pays_data = [
    ('Sénégal', 'SEN', 'afrique', 'cedeao', 17763163, 27625),
    ('France', 'FRA', 'europe', 'ue', 67390000, 2778090),
    ('Chine', 'CHN', 'asie', 'autre', 1425671352, 17734063),
    ('Inde', 'IND', 'asie', 'autre', 1428627663, 3385090),
    ('Nigéria', 'NGA', 'afrique', 'cedeao', 223804632, 477386),
    ('Côte d\'Ivoire', 'CIV', 'afrique', 'cedeao', 28160542, 70019),
    ('Mali', 'MLI', 'afrique', 'cedeao', 22593590, 19144),
    ('Espagne', 'ESP', 'europe', 'ue', 47420000, 1397509),
    ('Pays-Bas', 'NLD', 'europe', 'ue', 17590000, 1009346),
    ('États-Unis', 'USA', 'amerique_nord', 'alena', 331900000, 25462700),
    ('Brésil', 'BRA', 'amerique_sud', 'mercosur', 214300000, 1920100),
    ('Turquie', 'TUR', 'asie', 'autre', 85280000, 905988),
    ('Maroc', 'MAR', 'afrique', 'ua', 37080000, 134180),
    ('Allemagne', 'DEU', 'europe', 'ue', 83200000, 4072192),
    ('Thaïlande', 'THA', 'asie', 'asean', 71800000, 495341),
    ('Ghana', 'GHA', 'afrique', 'cedeao', 33470000, 77594),
    ('Guinée', 'GIN', 'afrique', 'cedeao', 13860000, 16091),
    ('Gambie', 'GMB', 'afrique', 'cedeao', 2640000, 2078),
    ('Mauritanie', 'MRT', 'afrique', 'ua', 4615000, 9961),
    ('Japon', 'JPN', 'asie', 'autre', 125700000, 4231141),
    ('Italie', 'ITA', 'europe', 'ue', 59110000, 2010432),
    ('Royaume-Uni', 'GBR', 'europe', 'autre', 67330000, 3070668),
]

pays_objects = {}
for nom, code, continent, bloc, pop, pib in pays_data:
    p = Pays.objects.create(
        nom=nom, code_iso=code, continent=continent,
        bloc_economique=bloc, population=pop, pib=Decimal(str(pib))
    )
    pays_objects[code] = p

senegal = pays_objects['SEN']

# ===================== CATEGORIES =====================
print("Création des catégories...")
categories_data = [
    ('Produits alimentaires', '02-23', 'Céréales, viandes, poissons, fruits, légumes'),
    ('Produits pétroliers', '27', 'Pétrole brut, carburants, gaz'),
    ('Produits chimiques', '28-38', 'Engrais, médicaments, produits chimiques'),
    ('Matériaux de construction', '68-70', 'Ciment, fer, acier, verre'),
    ('Machines et équipements', '84-85', 'Machines industrielles, équipements électriques'),
    ('Véhicules et transport', '86-89', 'Voitures, camions, pièces détachées'),
    ('Produits miniers', '25-26', 'Phosphates, or, zircon, minerais'),
    ('Textiles et habillement', '50-63', 'Coton, tissus, vêtements'),
    ('Produits halieutiques', '03', 'Poissons, crustacés, mollusques'),
    ('Bois et papier', '44-49', 'Bois, papier, carton'),
]

cat_objects = {}
for nom, code, desc in categories_data:
    c = CategorieProduit.objects.create(nom=nom, code_sh=code, description=desc)
    cat_objects[nom] = c

# ===================== PRODUITS =====================
print("Création des produits...")
produits_data = [
    ('Riz brisé', 'Produits alimentaires', 'tonne'),
    ('Blé et farine de blé', 'Produits alimentaires', 'tonne'),
    ('Sucre', 'Produits alimentaires', 'tonne'),
    ('Huile végétale', 'Produits alimentaires', 'litre'),
    ('Lait en poudre', 'Produits alimentaires', 'kg'),
    ('Pétrole brut', 'Produits pétroliers', 'baril'),
    ('Gasoil', 'Produits pétroliers', 'litre'),
    ('Essence', 'Produits pétroliers', 'litre'),
    ('Engrais chimiques', 'Produits chimiques', 'tonne'),
    ('Médicaments', 'Produits chimiques', 'kg'),
    ('Ciment', 'Matériaux de construction', 'tonne'),
    ('Fer et acier', 'Matériaux de construction', 'tonne'),
    ('Machines industrielles', 'Machines et équipements', 'unite'),
    ('Équipements électriques', 'Machines et équipements', 'unite'),
    ('Véhicules automobiles', 'Véhicules et transport', 'unite'),
    ('Pièces détachées auto', 'Véhicules et transport', 'kg'),
    ('Acide phosphorique', 'Produits miniers', 'tonne'),
    ('Or', 'Produits miniers', 'kg'),
    ('Zircon', 'Produits miniers', 'tonne'),
    ('Phosphates', 'Produits miniers', 'tonne'),
    ('Poisson frais', 'Produits halieutiques', 'tonne'),
    ('Poisson transformé', 'Produits halieutiques', 'tonne'),
    ('Crevettes', 'Produits halieutiques', 'kg'),
    ('Coton brut', 'Textiles et habillement', 'tonne'),
    ('Tissus imprimés', 'Textiles et habillement', 'unite'),
    ('Arachide', 'Produits alimentaires', 'tonne'),
    ('Noix de cajou', 'Produits alimentaires', 'tonne'),
]

produit_objects = {}
for nom, cat_nom, unite in produits_data:
    p = Produit.objects.create(
        nom=nom, categorie=cat_objects[cat_nom], unite_mesure=unite
    )
    produit_objects[nom] = p

# ===================== TRANSACTIONS =====================
print("Génération des transactions...")

# Prix de base par produit (en FCFA)
prix_base = {
    'Riz brisé': 250000, 'Blé et farine de blé': 200000, 'Sucre': 350000,
    'Huile végétale': 800, 'Lait en poudre': 2500, 'Pétrole brut': 45000,
    'Gasoil': 650, 'Essence': 700, 'Engrais chimiques': 300000,
    'Médicaments': 15000, 'Ciment': 60000, 'Fer et acier': 450000,
    'Machines industrielles': 25000000, 'Équipements électriques': 5000000,
    'Véhicules automobiles': 12000000, 'Pièces détachées auto': 8000,
    'Acide phosphorique': 350000, 'Or': 35000000, 'Zircon': 200000,
    'Phosphates': 80000, 'Poisson frais': 1500000, 'Poisson transformé': 2000000,
    'Crevettes': 12000, 'Coton brut': 800000, 'Tissus imprimés': 3500,
    'Arachide': 400000, 'Noix de cajou': 1200000,
}

# Produits principalement importés et leurs fournisseurs
imports_config = {
    'Riz brisé': ['IND', 'THA', 'CHN', 'BRA'],
    'Blé et farine de blé': ['FRA', 'USA', 'TUR'],
    'Sucre': ['BRA', 'FRA', 'IND'],
    'Huile végétale': ['MLI', 'CIV', 'ESP'],
    'Lait en poudre': ['FRA', 'NLD', 'DEU'],
    'Pétrole brut': ['NGA', 'USA', 'GBR'],
    'Gasoil': ['NGA', 'NLD', 'FRA'],
    'Essence': ['NGA', 'NLD'],
    'Engrais chimiques': ['MAR', 'CHN', 'IND'],
    'Médicaments': ['FRA', 'IND', 'CHN', 'DEU'],
    'Ciment': ['TUR', 'CHN', 'ESP'],
    'Fer et acier': ['CHN', 'TUR', 'ITA'],
    'Machines industrielles': ['CHN', 'FRA', 'DEU', 'JPN'],
    'Équipements électriques': ['CHN', 'FRA', 'JPN'],
    'Véhicules automobiles': ['FRA', 'JPN', 'DEU', 'USA'],
    'Pièces détachées auto': ['CHN', 'FRA', 'JPN'],
    'Tissus imprimés': ['CHN', 'IND', 'TUR'],
}

# Produits principalement exportés et leurs destinations
exports_config = {
    'Acide phosphorique': ['IND', 'FRA', 'ESP', 'NLD'],
    'Or': ['CHN', 'GBR', 'USA'],
    'Zircon': ['CHN', 'ESP', 'FRA'],
    'Phosphates': ['IND', 'CHN', 'NLD'],
    'Poisson frais': ['FRA', 'ESP', 'ITA', 'CIV'],
    'Poisson transformé': ['CIV', 'GHA', 'MLI', 'GIN'],
    'Crevettes': ['FRA', 'ESP', 'ITA'],
    'Arachide': ['CHN', 'FRA', 'NLD'],
    'Noix de cajou': ['IND', 'CHN', 'USA'],
    'Coton brut': ['CHN', 'IND', 'THA'],
    'Ciment': ['MLI', 'GMB', 'GIN', 'MRT'],
}

transports = ['maritime', 'aerien', 'terrestre']
transport_weights = [0.6, 0.15, 0.25]

date_debut = date(2025, 1, 1)
compteur = 1

# Générer les importations
for produit_nom, fournisseurs in imports_config.items():
    produit = produit_objects[produit_nom]
    base_prix = prix_base[produit_nom]

    for mois in range(12):
        nb_transactions = random.randint(2, 5)
        for _ in range(nb_transactions):
            pays_code = random.choice(fournisseurs)
            pays_fournisseur = pays_objects[pays_code]

            prix = Decimal(str(base_prix)) * Decimal(str(random.uniform(0.8, 1.2)))
            prix = prix.quantize(Decimal('0.01'))
            quantite = Decimal(str(random.randint(50, 5000)))
            valeur = prix * quantite

            jour = random.randint(1, 28)
            date_t = date_debut + timedelta(days=mois * 30 + jour)

            transport = random.choices(transports, weights=transport_weights, k=1)[0]
            # Pays limitrophes = terrestre
            if pays_code in ['MLI', 'GMB', 'GIN', 'MRT']:
                transport = 'terrestre'

            Transaction.objects.create(
                type_transaction='importation',
                produit=produit,
                pays_origine=pays_fournisseur,
                pays_destination=senegal,
                quantite=quantite,
                prix_unitaire=prix,
                valeur_totale=valeur,
                date_transaction=date_t,
                numero_declaration=f"IMP-2025-{compteur:05d}",
                mode_transport=transport,
                statut='valide',
            )
            compteur += 1

# Générer les exportations
for produit_nom, destinations in exports_config.items():
    produit = produit_objects[produit_nom]
    base_prix = prix_base[produit_nom]

    for mois in range(12):
        nb_transactions = random.randint(1, 4)
        for _ in range(nb_transactions):
            pays_code = random.choice(destinations)
            pays_dest = pays_objects[pays_code]

            prix = Decimal(str(base_prix)) * Decimal(str(random.uniform(0.85, 1.15)))
            prix = prix.quantize(Decimal('0.01'))
            quantite = Decimal(str(random.randint(30, 3000)))
            valeur = prix * quantite

            jour = random.randint(1, 28)
            date_t = date_debut + timedelta(days=mois * 30 + jour)

            transport = random.choices(transports, weights=transport_weights, k=1)[0]
            if pays_code in ['MLI', 'GMB', 'GIN', 'MRT']:
                transport = 'terrestre'

            Transaction.objects.create(
                type_transaction='exportation',
                produit=produit,
                pays_origine=senegal,
                pays_destination=pays_dest,
                quantite=quantite,
                prix_unitaire=prix,
                valeur_totale=valeur,
                date_transaction=date_t,
                numero_declaration=f"EXP-2025-{compteur:05d}",
                mode_transport=transport,
                statut='valide',
            )
            compteur += 1

# Injecter quelques anomalies (prix très élevés ou volumes inhabituels)
print("Injection d'anomalies...")
anomaly_products = ['Riz brisé', 'Or', 'Pétrole brut', 'Crevettes', 'Médicaments']
for prod_nom in anomaly_products:
    produit = produit_objects[prod_nom]
    base = prix_base[prod_nom]

    # Anomalie de prix (x3 ou x0.2)
    pays_code = random.choice(list(pays_objects.keys()))
    while pays_code == 'SEN':
        pays_code = random.choice(list(pays_objects.keys()))

    facteur = random.choice([3.0, 0.2])
    prix = Decimal(str(base * facteur)).quantize(Decimal('0.01'))
    qte = Decimal(str(random.randint(100, 500)))

    Transaction.objects.create(
        type_transaction=random.choice(['importation', 'exportation']),
        produit=produit,
        pays_origine=pays_objects[pays_code] if random.random() > 0.5 else senegal,
        pays_destination=senegal if random.random() > 0.5 else pays_objects[pays_code],
        quantite=qte,
        prix_unitaire=prix,
        valeur_totale=prix * qte,
        date_transaction=date(2025, random.randint(1, 12), random.randint(1, 28)),
        numero_declaration=f"ANO-2025-{compteur:05d}",
        mode_transport='maritime',
        statut='valide',
    )
    compteur += 1

nb_total = Transaction.objects.count()
print(f"\nTerminé ! {nb_total} transactions créées.")
print(f"  - {Transaction.objects.filter(type_transaction='importation').count()} importations")
print(f"  - {Transaction.objects.filter(type_transaction='exportation').count()} exportations")
print(f"  - {Pays.objects.count()} pays")
print(f"  - {Produit.objects.count()} produits")
print(f"  - {CategorieProduit.objects.count()} catégories")
