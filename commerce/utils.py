from .models import ProfilUtilisateur


def get_user_role(user):
    """Retourne le rôle de l'utilisateur (admin par défaut pour superuser)."""
    if user.is_superuser:
        return 'admin'
    try:
        return user.profil.role
    except ProfilUtilisateur.DoesNotExist:
        return 'client'
