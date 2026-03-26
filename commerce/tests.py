from decimal import Decimal
from datetime import date

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Pays, CategorieProduit, Produit, Transaction, ProfilUtilisateur


class ModelsTestCase(TestCase):
    def setUp(self):
        self.senegal = Pays.objects.create(
            nom="Sénégal", code_iso="SEN", continent="afrique", bloc_economique="cedeao"
        )
        self.france = Pays.objects.create(
            nom="France", code_iso="FRA", continent="europe", bloc_economique="ue"
        )
        self.categorie = CategorieProduit.objects.create(
            nom="Céréales", code_sh="10", description="Chapitre 10"
        )
        self.produit = Produit.objects.create(
            nom="Riz brisé", categorie=self.categorie, unite_mesure="tonne"
        )

    def test_pays_str(self):
        self.assertEqual(str(self.senegal), "Sénégal (SEN)")

    def test_categorie_str(self):
        self.assertEqual(str(self.categorie), "10 - Céréales")

    def test_produit_str(self):
        self.assertEqual(str(self.produit), "Riz brisé")

    def test_transaction_creation(self):
        t = Transaction.objects.create(
            type_transaction='importation',
            produit=self.produit,
            pays_origine=self.france,
            pays_destination=self.senegal,
            quantite=Decimal('1000'),
            prix_unitaire=Decimal('500'),
            valeur_totale=Decimal('500000'),
            date_transaction=date(2024, 6, 15),
            numero_declaration='IMP-TEST-001',
            mode_transport='maritime',
            statut='valide',
        )
        self.assertEqual(t.get_type_transaction_display(), "Importation")
        self.assertEqual(t.valeur_totale, Decimal('500000'))

    def test_transaction_ordering(self):
        t1 = Transaction.objects.create(
            type_transaction='importation', produit=self.produit,
            pays_origine=self.france, pays_destination=self.senegal,
            quantite=100, prix_unitaire=500, valeur_totale=50000,
            date_transaction=date(2024, 1, 1), numero_declaration='T1',
            mode_transport='maritime', statut='valide',
        )
        t2 = Transaction.objects.create(
            type_transaction='exportation', produit=self.produit,
            pays_origine=self.senegal, pays_destination=self.france,
            quantite=200, prix_unitaire=600, valeur_totale=120000,
            date_transaction=date(2024, 6, 1), numero_declaration='T2',
            mode_transport='aerien', statut='valide',
        )
        transactions = list(Transaction.objects.all())
        self.assertEqual(transactions[0], t2)


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        ProfilUtilisateur.objects.create(user=self.user, role='admin')

        self.senegal = Pays.objects.create(
            nom="Sénégal", code_iso="SEN", continent="afrique", bloc_economique="cedeao"
        )
        self.france = Pays.objects.create(
            nom="France", code_iso="FRA", continent="europe", bloc_economique="ue"
        )
        self.categorie = CategorieProduit.objects.create(
            nom="Céréales", code_sh="10"
        )
        self.produit = Produit.objects.create(
            nom="Riz brisé", categorie=self.categorie, unite_mesure="tonne"
        )
        self.transaction = Transaction.objects.create(
            type_transaction='importation', produit=self.produit,
            pays_origine=self.france, pays_destination=self.senegal,
            quantite=1000, prix_unitaire=500, valeur_totale=500000,
            date_transaction=date(2024, 6, 15), numero_declaration='IMP-TEST-001',
            mode_transport='maritime', statut='valide',
        )

    def test_login_required(self):
        urls = ['dashboard', 'transactions', 'balance', 'top_produits', 'anomalies',
                'sankey', 'codes_sh', 'blocs', 'series_temporelles']
        for url_name in urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)

    def test_dashboard(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')

    def test_dashboard_filtre_annee(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'), {'annee': '2024'})
        self.assertEqual(response.status_code, 200)

    def test_transactions_list(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('transactions'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'IMP-TEST-001')

    def test_transactions_filtre_type(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('transactions'), {'type': 'importation'})
        self.assertContains(response, 'Riz brisé')

    def test_transaction_create(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('transaction_create'))
        self.assertEqual(response.status_code, 200)

    def test_transaction_create_post(self):
        self.client.login(username='testuser', password='testpass123')
        data = {
            'type_transaction': 'exportation',
            'produit': self.produit.pk,
            'pays_origine': self.senegal.pk,
            'pays_destination': self.france.pk,
            'quantite': '500',
            'prix_unitaire': '1000',
            'date_transaction': '2024-07-01',
            'mode_transport': 'maritime',
            'statut': 'valide',
        }
        response = self.client.post(reverse('transaction_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 2)

    def test_transaction_edit(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('transaction_edit', args=[self.transaction.pk]))
        self.assertEqual(response.status_code, 200)

    def test_transaction_delete(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('transaction_delete', args=[self.transaction.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_balance(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('balance'))
        self.assertEqual(response.status_code, 200)

    def test_analyse_pays(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('analyse_pays'), {'pays': self.france.pk})
        self.assertEqual(response.status_code, 200)

    def test_top_produits(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('top_produits'))
        self.assertEqual(response.status_code, 200)

    def test_anomalies(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('anomalies'))
        self.assertEqual(response.status_code, 200)

    def test_sankey(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('sankey'))
        self.assertEqual(response.status_code, 200)

    def test_codes_sh(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('codes_sh'))
        self.assertEqual(response.status_code, 200)

    def test_blocs(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('blocs'))
        self.assertEqual(response.status_code, 200)

    def test_series_temporelles(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('series_temporelles'))
        self.assertEqual(response.status_code, 200)

    def test_export_csv_transactions(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('export_csv'), {'type': 'transactions'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_export_csv_balance(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('export_csv'), {'type': 'balance'})
        self.assertEqual(response.status_code, 200)

    def test_login_view(self):
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'testpass123'})
        self.assertEqual(response.status_code, 302)

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
