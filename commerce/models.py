from django.db import models
from django.contrib.auth.models import User


class ProfilUtilisateur(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('client', 'Client'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')

    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'


class Pays(models.Model):
    CONTINENT_CHOICES = [
        ('afrique', 'Afrique'),
        ('europe', 'Europe'),
        ('asie', 'Asie'),
        ('amerique_nord', 'Amérique du Nord'),
        ('amerique_sud', 'Amérique du Sud'),
        ('oceanie', 'Océanie'),
    ]

    BLOC_CHOICES = [
        ('cedeao', 'CEDEAO'),
        ('ue', 'Union Européenne'),
        ('ua', 'Union Africaine'),
        ('asean', 'ASEAN'),
        ('mercosur', 'MERCOSUR'),
        ('alena', 'ALENA/ACEUM'),
        ('autre', 'Autre'),
    ]

    nom = models.CharField(max_length=100)
    code_iso = models.CharField(max_length=3, unique=True)
    continent = models.CharField(max_length=20, choices=CONTINENT_CHOICES)
    bloc_economique = models.CharField(max_length=20, choices=BLOC_CHOICES, default='autre')
    population = models.BigIntegerField(default=0)
    pib = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        ordering = ['continent', 'nom']
        verbose_name_plural = 'Pays'

    def __str__(self):
        return f"{self.nom} ({self.code_iso})"


class CategorieProduit(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    code_sh = models.CharField(max_length=10, verbose_name="Code SH")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['code_sh']
        verbose_name = 'Catégorie de produit'
        verbose_name_plural = 'Catégories de produits'

    def __str__(self):
        return f"{self.code_sh} - {self.nom}"


class Produit(models.Model):
    UNITE_CHOICES = [
        ('kg', 'Kilogramme'),
        ('tonne', 'Tonne'),
        ('litre', 'Litre'),
        ('unite', 'Unité'),
        ('m3', 'Mètre cube'),
        ('baril', 'Baril'),
    ]

    nom = models.CharField(max_length=200)
    categorie = models.ForeignKey(CategorieProduit, on_delete=models.CASCADE, related_name='produits')
    unite_mesure = models.CharField(max_length=10, choices=UNITE_CHOICES)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['categorie', 'nom']

    def __str__(self):
        return self.nom


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('importation', 'Importation'),
        ('exportation', 'Exportation'),
    ]

    TRANSPORT_CHOICES = [
        ('maritime', 'Maritime'),
        ('aerien', 'Aérien'),
        ('terrestre', 'Terrestre'),
        ('ferroviaire', 'Ferroviaire'),
    ]

    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
    ]

    type_transaction = models.CharField(max_length=15, choices=TYPE_CHOICES)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='transactions')
    pays_origine = models.ForeignKey(Pays, on_delete=models.CASCADE, related_name='transactions_origine')
    pays_destination = models.ForeignKey(Pays, on_delete=models.CASCADE, related_name='transactions_destination')
    quantite = models.DecimalField(max_digits=15, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=15, decimal_places=2)
    valeur_totale = models.DecimalField(max_digits=20, decimal_places=2)
    date_transaction = models.DateField()
    numero_declaration = models.CharField(max_length=50, unique=True)
    mode_transport = models.CharField(max_length=15, choices=TRANSPORT_CHOICES)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='valide')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['-date_transaction']
        indexes = [
            models.Index(fields=['type_transaction', 'statut']),
            models.Index(fields=['date_transaction']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"{self.get_type_transaction_display()} - {self.produit.nom} ({self.date_transaction})"
