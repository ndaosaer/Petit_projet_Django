# Systeme de Suivi Import / Export du Senegal

Application web Django pour l'analyse et la visualisation des flux commerciaux du Senegal a partir de donnees officielles de l'ONU.

Projet realise dans le cadre du cours Django AS3 — Groupe 5 — ENSAE Dakar — Mars 2026.

---

## Sommaire

- [Presentation](#presentation)
- [Fonctionnalites](#fonctionnalites)
- [Architecture technique](#architecture-technique)
- [Modele de donnees](#modele-de-donnees)
- [Securite et gestion des roles](#securite-et-gestion-des-roles)
- [Donnees reelles — UN Comtrade](#donnees-reelles--un-comtrade)
- [Installation](#installation)
- [Chargement des donnees](#chargement-des-donnees)
- [Tests](#tests)
- [Structure du projet](#structure-du-projet)
- [Deploiement](#deploiement)
- [Limites et perspectives](#limites-et-perspectives)
- [Auteurs](#auteurs)

---

## Presentation

Le Senegal est un acteur majeur du commerce en Afrique de l'Ouest. Ce projet repond au besoin de disposer d'un outil moderne pour visualiser, analyser et detecter des anomalies dans les donnees d'import et d'export du pays.

L'application est developpee avec Django et utilise des donnees reelles issues de l'API officielle UN Comtrade des Nations Unies. Elle permet notamment de calculer la balance commerciale, d'identifier les principaux partenaires et produits echanges, et de generer des visualisations interactives.

---

## Fonctionnalites

### Analyse

**Dashboard** — Vue d'ensemble avec KPIs principaux, evolution mensuelle des flux, classement des dix premiers partenaires commerciaux. Filtres par annee et par periode.

**Balance commerciale** — Calcul automatique de l'excedent ou du deficit par pays et par bloc economique. Taux de couverture et graphiques comparatifs.

**Top produits** — Classement des marchandises les plus importees et exportees. Repartition par categorie sous forme de donut charts.

**Series temporelles** — Moyennes mobiles sur trois mois, variations mensuelles en pourcentage, balance mensuelle avec tendances.

**Analyse par pays** — Detail des echanges avec chaque partenaire : top produits, evolution historique, informations generales sur le pays.

**Flux Sankey** — Diagramme interactif Plotly representant les flux commerciaux origine/destination avec les volumes correspondants.

### Gestion et outils

**Codes du Systeme Harmonise (SH)** — Analyse des donnees par chapitres SH, graphiques comparatifs par categorie de produits.

**Blocs economiques** — Comparaison des echanges par regroupement regional : CEDEAO, Union Europeenne, ASEAN, MERCOSUR, et autres.

**Detection d'anomalies** — Algorithme statistique base sur la methode des deux ecarts-types. Identifie automatiquement les transactions avec des prix ou volumes anormaux.

**CRUD Transactions** — Creation, modification et suppression de transactions (administrateurs uniquement). Numerotation sequentielle automatique et calcul automatique de la valeur totale.

**Export CSV** — Export des transactions, balances et produits en fichier CSV (administrateurs uniquement).

**Pagination et filtres** — Navigation par pages de 25 resultats. Filtres par type d'operation, par pays et par periode.

---

## Architecture technique

L'application suit l'architecture MVT (Model — View — Template) de Django.

| Composant | Technologie | Role |
|---|---|---|
| Framework backend | Django 6.0 | Logique metier, routage, authentification |
| Base de donnees | SQLite | Stockage relationnel |
| Graphiques standard | Chart.js | Courbes, histogrammes, donut charts |
| Diagrammes avances | Plotly.js | Flux Sankey interactifs |
| Templates | HTML / CSS | Interface utilisateur |

Le navigateur envoie des requetes HTTP qui sont routees via `urls.py` vers les vues (`views.py`). Les vues interrogent les modeles (`models.py`) pour acceder a la base de donnees, puis retournent les donnees aux templates HTML qui generent la page finale.

---

## Modele de donnees

L'application repose sur cinq modeles Django.

**Transaction** — Coeur du systeme. Enregistre chaque operation commerciale avec ses attributs : type (import/export), produit, pays d'origine, pays de destination, quantite, prix unitaire, valeur totale, date, mode de transport, statut, date de creation.

**Pays** — Partenaires commerciaux. Contient le nom, le code ISO, le continent, le bloc economique d'appartenance (CEDEAO, UE...), la population et le PIB.

**Produit** — Marchandises echangees. Lie a une categorie via cle etrangere, avec l'unite de mesure associee.

**CategorieProduit** — Classification des produits selon le Systeme Harmonise international. Contient le nom, le code SH et une description.

**ProfilUtilisateur** — Extension du modele utilisateur Django. Gere les roles d'acces : administrateur ou client.

Chiffres cles : 5 modeles, 3 index de base de donnees, plus de 25 000 transactions, plus de 100 pays references.

---

## Securite et gestion des roles

### Profils d'acces

**Administrateur**
- Acces complet a toutes les pages de l'application
- Creation, modification et suppression de transactions (CRUD)
- Export CSV des transactions, balances et produits
- Acces aux analyses avancees : anomalies, Sankey, series temporelles, blocs economiques, codes SH

**Client**
- Dashboard avec KPIs et graphiques
- Consultation de la liste des transactions (lecture seule)
- Balance commerciale par pays
- Top produits importes et exportes
- Pas d'acces aux fonctions d'ecriture ni aux analyses avancees

### Mesures de securite implementees

- Protection CSRF avec deconnexion en methode POST (`@require_POST`)
- Validation des mots de passe par Django
- Unicite des adresses email verifiee a l'inscription
- Decorateur personnalise `@admin_required` protegeant les vues sensibles
- Configuration de cookies securises pour l'environnement de production

---

## Donnees reelles — UN Comtrade

Les donnees sont issues de l'API officielle de la base de donnees UN Comtrade des Nations Unies, reference internationale pour les statistiques du commerce mondial.

Cle API gratuite disponible sur : https://comtradedeveloper.un.org

### Pipeline de chargement

1. **Appel API** — Requetes GET avec le code pays `SEN` (Senegal) pour les annees 2023 et 2024.
2. **Traitement** — Repartition des donnees annuelles sur 12 mois et conversion des montants de USD en FCFA (taux fixe : 1 USD = 600 FCFA).
3. **Enrichissement** — Association de noms de produits specifiques selon les chapitres du Systeme Harmonise.
4. **Chargement** — Insertion en base SQLite avec respect des contraintes de cles etrangeres.

---

## Installation

### Prerequis

- Python 3.10 ou superieur
- pip

### Etapes

Cloner le depot :

```bash
git clone https://github.com/ndaosaer/Petit_projet_Django.git
cd Petit_projet_Django
```

Creer et activer un environnement virtuel :

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

Installer les dependances :

```bash
pip install -r requirements.txt
```

Appliquer les migrations :

```bash
python manage.py migrate
```

Creer un superutilisateur :

```bash
python manage.py createsuperuser
```

Lancer le serveur de developpement :

```bash
python manage.py runserver
```

L'application est accessible sur : http://127.0.0.1:8000

---

## Chargement des donnees

### Donnees de demonstration

Pour charger un jeu de donnees fictives afin de tester rapidement l'application :

```bash
python create_sample_data.py
```

### Donnees reelles (UN Comtrade)

Pour charger les donnees officielles des Nations Unies (necessite une cle API) :

```bash
python load_real_data.py
```

Renseigner votre cle API UN Comtrade dans le script avant execution.

### Comptes par defaut (apres chargement des donnees de demonstration)

| Role | Identifiant | Mot de passe |
|---|---|---|
| Administrateur | `admin` | `admin123` |
| Client | `client` | `client123` |

---

## Tests

L'application dispose de 26 tests unitaires. Pour les executer :

```bash
python manage.py test commerce
```

Pour un affichage detaille :

```bash
python manage.py test commerce --verbosity=2
```

---

## Structure du projet

```
Petit_projet_Django/
├── commerce/
│   ├── models.py               # 5 modeles de donnees (133 lignes)
│   ├── views.py                # 14 vues Django (850+ lignes)
│   ├── forms.py                # 3 formulaires
│   ├── utils.py                # Fonction utilitaire get_user_role()
│   ├── context_processors.py   # Processeur de contexte global
│   ├── admin.py                # 5 classes ModelAdmin
│   └── tests.py                # 26 tests unitaires
├── suivi_import_export/
│   ├── settings.py             # Configuration Django
│   ├── urls.py                 # Routage principal
│   └── templates/              # 15 templates HTML
├── create_sample_data.py       # Script de generation de donnees fictives
├── load_real_data.py           # Script de chargement via API UN Comtrade
├── manage.py
├── requirements.txt
├── DEPLOY.md                   # Guide de deploiement sur PythonAnywhere
└── db.sqlite3                  # Base de donnees (25 000+ transactions)
```

Metriques du projet : 14 vues Django, 15 templates HTML, 26 tests unitaires, 12 graphiques interactifs, 3 types d'exports CSV.

---

## Deploiement

Un guide detaille de deploiement sur PythonAnywhere est disponible dans le fichier `DEPLOY.md` a la racine du projet.

Les grandes etapes sont les suivantes :

1. Creer un compte sur https://www.pythonanywhere.com
2. Uploader le projet via ZIP ou via Git
3. Creer un environnement virtuel et installer les dependances
4. Configurer l'application web et le fichier WSGI
5. Declarer le repertoire des fichiers statiques
6. Appliquer les migrations et collecter les statiques
7. Recharger l'application

---

## Limites et perspectives

### Limites actuelles

- Les donnees annuelles de Comtrade ont ete reparties sur 12 mois par estimation, avec une marge d'erreur d'environ 30 %. Les donnees mensuelles sont disponibles uniquement via l'API premium.
- Le mode de transport n'etant pas fourni par Comtrade, il a ete assigne aleatoirement dans le script de chargement.
- Le taux de change USD/FCFA est fixe a 600, sans prise en compte des variations reelles.
- Les donnees couvrent uniquement les annees 2023 et 2024.
- L'application ne dispose pas d'une API REST pour une consommation externe.

### Perspectives d'amelioration

- Integrer les donnees mensuelles via l'acces premium a l'API UN Comtrade.
- Ajouter une API REST avec Django REST Framework pour exposer les donnees a des applications tierces.
- Deployer en production sur une plateforme cloud (Heroku, Railway ou similaire).
- Mettre en place un systeme de cache avec Redis pour optimiser les calculs intensifs.
- Developper une application mobile connectee via l'API REST.
- Integrer un taux de change dynamique via une API financiere.

---

## Auteurs

Groupe 5 — ENSAE Dakar — Cours Django AS3 — Mars 2026

Donnees sources : UN Comtrade Database — Nations Unies (https://comtrade.un.org)
