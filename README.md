# Comité des Fêtes — Backoffice Wagtail

Application de gestion pour un Comité des Fêtes, construite avec **Django 6.0**, **Wagtail 7.3** et **Tailwind CSS 4**.

> 🚧 Projet en début de développement.

## 🎯 Objectif

Fournir aux membres du bureau un espace centralisé pour :

- organiser les **événements** (fêtes, réunions, assemblées…) sur une timeline chronologique ;
- rattacher des **documents** (factures, relevés, assurances…) classés par **collection Wagtail** ;
- associer des **images** à chaque événement ;
- rédiger des **notes et comptes-rendus** via un éditeur riche (StreamField).

La page d'index des événements est publique. L'accès aux fiches détaillées est contrôlé par les **restrictions de page Wagtail** (`PageViewRestriction`).

## 📦 Structure du projet

| Dossier | Rôle |
|---------|------|
| `core/` | Modèle [`CustomDocument`](core/models.py) — document Wagtail étendu avec date et notes |
| `events/` | [`EventIndexPage`](events/models.py) (liste paginée, timeline) et [`EventPage`](events/models.py) (fiche événement) avec [`EventImage`](events/models.py) et [`EventDocument`](events/models.py) |
| `home/` | [`HomePage`](home/models.py) — page d'accueil (non utilisée pour le moment) |
| `search/` | Recherche full-text Wagtail (non utilisée pour le moment) |
| `project/` | Configuration Django/Wagtail, templates de base, fichiers statiques |

## ⚙️ Fonctionnement

### Documents personnalisés

Le modèle [`CustomDocument`](core/models.py) étend `AbstractDocument` de Wagtail et ajoute :

- une **date de document** (`document_date`) ;
- un champ **notes**.

Les documents sont organisés via les **collections Wagtail** natives (pas de modèle de catégorie dédié). Le modèle est déclaré via `WAGTAILDOCS_DOCUMENT_MODEL` dans les settings.

### Événements

- [`EventIndexPage`](events/models.py) — page parente qui liste ses enfants `EventPage` avec pagination configurable (`events_per_page`). Le contexte expose un flag `can_view_details` : seuls les éditeurs/modérateurs Wagtail voient le lien « Voir détails » sur l'index.
- [`EventPage`](events/models.py) — fiche détaillée d'un événement. Le contexte injecte les images, les documents groupés par collection via [`get_documents_by_collection()`](events/models.py), et un lien d'édition Wagtail admin pour les utilisateurs autorisés.

### Hiérarchie des pages

```
HomePage
  └── EventIndexPage
        └── EventPage (pas de sous-pages)
```

Les règles `parent_page_types` et `subpage_types` sont appliquées sur chaque modèle.

### Front-end

- **Tailwind CSS 4** compilé via `@tailwindcss/cli`.
- Source : [`project/static/src/input.css`](project/static/src/input.css) → compilé vers `project/static/css/output.css`.
- Chargé dans [`base.html`](project/templates/base.html) via `{% static 'css/output.css' %}`.
- Palette personnalisée **blason** (bleu azur) définie dans `input.css`.

## 🛠️ Développement

```sh
# Terminal 1 — Tailwind (watch)
npm run dev

# Terminal 2 — Django
python manage.py runserver
```

Admin Wagtail : [http://localhost:8000/admin/](http://localhost:8000/admin/)

## ✅ Tests

| Fichier | Ce qui est testé |
|---------|-----------------|
| [`core/tests.py`](core/tests.py) | `CustomDocument` : `__str__`, collection par défaut, assignation à une collection personnalisée |
| [`events/tests.py`](events/tests.py) | Hiérarchie des pages · Rendu de l'index et pagination · Accès via `PageViewRestriction` · Visibilité du lien « Voir détails » (anonyme, utilisateur simple, superuser) · Groupement des documents par collection |

Un mixin partagé [`EventPageTreeMixin`](events/tests.py) construit l'arbre de pages pour tous les tests de l'app `events`.

```sh
python manage.py test
```