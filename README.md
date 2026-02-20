# Comité des Fêtes — Backoffice Wagtail

Application de gestion backoffice pour un Comité des Fêtes, construite avec **Django 6.0**, **Wagtail 7.3**, **Tailwind CSS 4.1** et **Vite 7.3**.

> 🚧 Projet en début de développement.

## 🎯 Objectif

Fournir aux membres du bureau d'un Comité des Fêtes un espace centralisé pour :

- organiser les **événements** (fêtes, réunions, assemblées…) sur une timeline chronologique ;
- rattacher des **documents** (factures, relevés bancaires, assurances, comptes-rendus…) classés par **catégorie** ;
- associer des **images** à chaque événement ;
- rédiger des **notes et comptes-rendus** via un éditeur riche (StreamField).

L'accès aux fiches événements est **réservé au staff** (403 pour les anonymes et les utilisateurs non-staff). La page d'index des événements reste publique.

## 📦 Structure du projet

| Dossier | Rôle |
|---------|------|
| **`core/`** | Modèles transversaux : [`CustomDocument`](core/models.py) (document avec date, catégorie, notes) et snippet [`DocumentCategory`](core/models.py) |
| **`events/`** | [`EventIndexPage`](events/models.py) (liste paginée + timeline) et [`EventPage`](events/models.py) (fiche événement staff-only), avec les orderables [`EventImage`](events/models.py) et [`EventDocument`](events/models.py) |
| **`home/`** | [`HomePage`](home/models.py) — page d'accueil (Inutilisé pour le moment, je le garde pour une éventuelle utilisation future) |
| **`search/`** | [Recherche full-text Wagtail](search/views.py) (Inutilisé pour le moment) |
| **`project/`** | Configuration Django/Wagtail, templates de base, fichiers statiques source |

## ⚙️ Fonctionnement

### Documents personnalisés

Le modèle [`CustomDocument`](core/models.py) étend `AbstractDocument` de Wagtail et ajoute :
- une **date de document** (`document_date`) ;
- une **catégorie** (FK vers [`DocumentCategory`](core/models.py), protégée par `PROTECT`) ;
- un champ **notes**.

Il est déclaré comme modèle de document Wagtail via `WAGTAILDOCS_DOCUMENT_MODEL` dans [project/settings/base.py](project/settings/base.py).

### Événements

- **[`EventIndexPage`](events/models.py)** : page parente qui liste ses enfants `EventPage` avec pagination configurable (`events_per_page`). Le template [event_index_page.html](events/templates/events/event_index_page.html) affiche une timeline verticale responsive avec les documents et notes en aperçu.
- **[`EventPage`](events/models.py)** : fiche détaillée d'un événement. Accès contrôlé dans [`serve()`](events/models.py) (staff uniquement). Le contexte injecte les images, les documents groupés par catégorie via [`get_documents_by_category()`](events/models.py), et un lien d'édition Wagtail admin pour les utilisateurs autorisés.

### Hiérarchie des pages

```
EventIndexPage
      └── EventPage (pas de sous-pages)
```

Les règles `parent_page_types` et `subpage_types` sont appliquées sur chaque modèle.

### Front-end

- **Tailwind CSS 4** compilé par **Vite** (config dans [vite.config.js](vite.config.js)).
- Intégration Django via **django-vite** ([base.html](project/templates/base.html) utilise `{% vite_hmr_client %}` et `{% vite_asset %}`).
- Les sources CSS scannent tous les templates des apps grâce aux directives `@source` dans [main.css](project/static/src/main.css).

## 🛠️ Développement

```sh
# Terminal 1 — Vite (hot-reload Tailwind)
npm run dev

# Terminal 2 — Django
python manage.py runserver
```

Admin Wagtail : [http://localhost:8000/admin/](http://localhost:8000/admin/)

## ✅ Tests

Le projet inclut une suite de tests unitaires couvrant :

| Fichier | Ce qui est testé |
|---------|-----------------|
| [core/tests.py](core/tests.py) | `DocumentCategory` (str, ordering) · `CustomDocument` (str, catégorie obligatoire, protection PROTECT à la suppression) |
| [events/tests.py](events/tests.py) | Hiérarchie des pages (`assertCanCreateAt`, `assertAllowedSubpageTypes`) · Rendu de l'index et pagination · Accès staff-only sur `EventPage` (403 anonyme/non-staff, 200 staff, template correct) · Groupement des documents par catégorie
Un **mixin partagé** [`EventPageTreeMixin`](events/tests.py) construit l'arbre de pages (root → index → event) pour les tests de l'app events.

Lancer les tests :

```sh
python manage.py test
```