from django.contrib import admin
from .models import Pays, CategorieProduit, Produit, Transaction, ProfilUtilisateur


@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)


@admin.register(Pays)
class PaysAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_iso', 'continent', 'bloc_economique', 'population')
    list_filter = ('continent', 'bloc_economique')
    search_fields = ('nom', 'code_iso')


@admin.register(CategorieProduit)
class CategorieProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_sh', 'description')
    search_fields = ('nom', 'code_sh')


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'unite_mesure')
    list_filter = ('categorie', 'unite_mesure')
    search_fields = ('nom',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('numero_declaration', 'type_transaction', 'produit', 'pays_origine',
                    'pays_destination', 'valeur_totale', 'date_transaction', 'statut')
    list_filter = ('type_transaction', 'mode_transport', 'statut', 'pays_origine__continent')
    search_fields = ('numero_declaration', 'produit__nom', 'pays_origine__nom', 'pays_destination__nom')
    date_hierarchy = 'date_transaction'
    readonly_fields = ('valeur_totale', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        obj.valeur_totale = obj.quantite * obj.prix_unitaire
        super().save_model(request, obj, form, change)
