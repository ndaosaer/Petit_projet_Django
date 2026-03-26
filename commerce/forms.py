from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Transaction


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, label="Nom d'utilisateur")
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirmer le mot de passe")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': "Nom d'utilisateur",
            'email': "Adresse email",
            'first_name': "Prénom",
            'last_name': "Nom",
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte avec cette adresse email existe déjà.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                self.add_error('password', e)
        return cleaned_data


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'type_transaction', 'produit', 'pays_origine', 'pays_destination',
            'quantite', 'prix_unitaire', 'date_transaction',
            'mode_transport', 'statut',
        ]
        labels = {
            'type_transaction': "Type",
            'produit': "Produit",
            'pays_origine': "Pays d'origine",
            'pays_destination': "Pays de destination",
            'quantite': "Quantité",
            'prix_unitaire': "Prix unitaire (FCFA)",
            'date_transaction': "Date",
            'mode_transport': "Mode de transport",
            'statut': "Statut",
        }
        widgets = {
            'date_transaction': forms.DateInput(attrs={'type': 'date'}),
        }

    def save(self, commit=True):
        from django.db import transaction as db_transaction
        instance = super().save(commit=False)
        instance.valeur_totale = instance.quantite * instance.prix_unitaire
        if not instance.numero_declaration:
            prefix = "IMP" if instance.type_transaction == 'importation' else "EXP"
            with db_transaction.atomic():
                last = (
                    Transaction.objects
                    .select_for_update()
                    .filter(numero_declaration__startswith=f"{prefix}-{instance.date_transaction.year}-")
                    .order_by('-numero_declaration')
                    .first()
                )
                if last:
                    try:
                        last_num = int(last.numero_declaration.split('-')[-1])
                        next_num = last_num + 1
                    except ValueError:
                        next_num = 1
                else:
                    next_num = 1
                instance.numero_declaration = f"{prefix}-{instance.date_transaction.year}-{next_num:05d}"
                if commit:
                    instance.save()
                return instance
        if commit:
            instance.save()
        return instance
