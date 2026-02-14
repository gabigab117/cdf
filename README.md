# Comité des Fêtes - Backoffice Wagtail (Je viens juste de commencer le développement)

Application de gestion backoffice pour un Comité des Fêtes, construite avec **Django** et **Wagtail CMS**.

## 🎯 Fonctionnalités

- **Gestion de documents** avec catégories personnalisables (relevés bancaires, factures, assurances, etc.)
- **Gestion d'événements** avec notes, comptes-rendus et documents rattachés
- **Collections Wagtail** pour organiser les documents administratifs
- **Interface d'administration** intuitive via Wagtail

## 🚀 Installation

```sh
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
npm install

# Migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Compiler les assets CSS (Tailwind)
npm run build
```

## 🛠️ Développement

```sh
# Lancer Vite en mode développement (Tailwind)
npm run dev

# Dans un autre terminal, lancer Django
python manage.py runserver
```

Accéder à l'interface admin : [http://localhost:8000/admin/](http://localhost:8000/admin/)

## 📦 Structure

- **`core/`** : Modèles personnalisés (CustomDocument, DocumentCategory)
- **`events/`** : Gestion des événements (EventPage)
- **`home/`** : Page d'accueil
- **`search/`** : Recherche Wagtail
- **`project/`** : Configuration Django

## 📝 Environnements

- **Développement** : `project/settings/dev.py`
- **Production** : `project/settings/production.py`

## 🔧 Technologies

- Django 6.0
- Wagtail 7.3
- Tailwind CSS 4.1
- Vite 7.3
