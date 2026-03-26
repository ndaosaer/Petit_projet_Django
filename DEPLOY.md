# Déploiement sur PythonAnywhere

## 1. Créer un compte
- Aller sur https://www.pythonanywhere.com
- Créer un compte gratuit (ex: `importexportsn`)
- L'URL sera : `importexportsn.pythonanywhere.com`

## 2. Uploader le projet

### Option A : Via ZIP (plus simple)
1. Compresser le dossier `suivi_import_export/` en ZIP
2. Sur PythonAnywhere : **Files** > Upload le ZIP
3. Ouvrir une console Bash et extraire :
```bash
cd ~
unzip suivi_import_export.zip
```

### Option B : Via GitHub
```bash
cd ~
git clone https://github.com/votre-repo/suivi_import_export.git
```

## 3. Créer un virtualenv
Dans la console Bash PythonAnywhere :
```bash
mkvirtualenv --python=/usr/bin/python3.12 myenv
pip install -r ~/suivi_import_export/requirements.txt
```

## 4. Configurer l'application Web
1. Aller dans **Web** tab
2. Cliquer **Add a new web app**
3. Choisir **Manual configuration** > **Python 3.12**
4. Configurer le **Virtualenv** : `/home/importexportsn/.virtualenvs/myenv`

## 5. Configurer le fichier WSGI
Cliquer sur le lien du fichier WSGI et remplacer le contenu par :
```python
import os
import sys

# Ajouter le projet au path
path = '/home/importexportsn/suivi_import_export'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'suivi_import_export.settings'
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_SECRET_KEY'] = 'VOTRE-CLE-SECRETE-ICI-GENERER-UNE-LONGUE'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

> Remplacer `importexportsn` par votre nom d'utilisateur PythonAnywhere

## 6. Configurer les fichiers statiques
Dans l'onglet **Web**, section **Static files** :

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/importexportsn/suivi_import_export/staticfiles` |

## 7. Appliquer les migrations et collecter les statiques
```bash
cd ~/suivi_import_export
python manage.py migrate
python manage.py collectstatic --noinput
```

## 8. Recharger
- Cliquer le bouton **Reload** dans l'onglet Web
- Visiter `https://importexportsn.pythonanywhere.com`

## Comptes par défaut
- **Admin** : `admin` / `admin123`
- **Client** : `client` / `client123`

## Dépannage
- **Erreur 500** : Vérifier les logs dans Web > Error log
- **Static files 404** : Vérifier le chemin dans la config Static files
- **Module not found** : Vérifier que le virtualenv est bien activé
