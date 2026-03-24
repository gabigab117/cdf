# Comité des Fêtes — Backoffice Wagtail

Application de gestion pour un Comité des Fêtes, construite avec **Django 6.0**, **Wagtail 7.3**, **Tailwind CSS 4** et **HTMX 2**.

> 🚧 Projet en développement actif.

## 🎯 Objectif

Fournir aux membres du bureau un espace centralisé pour :

- organiser les **événements** (fêtes, réunions, assemblées…) sur une timeline chronologique ;
- rattacher des **documents** (factures, relevés, assurances…) classés par **collection Wagtail** ;
- associer des **images** à chaque événement ;
- rédiger des **notes et comptes-rendus** via un éditeur riche (StreamField) ;
- gérer les **postes et affectations** de bénévoles par événement (Frites, BBQ, Caisse, Buvette…).

La page d'index des événements est publique. L'accès aux fiches détaillées est contrôlé par les **restrictions de page Wagtail** (`PageViewRestriction`). La gestion des postes est réservée aux **modérateurs** (superusers ou membres du groupe `Moderators`).

## 📦 Structure du projet

| Dossier | Rôle |
|---------|------|
| `core/` | Modèle [`CustomDocument`](core/models.py) — document Wagtail étendu avec date et notes |
| `events/` | Pages Wagtail ([`EventIndexPage`](events/models.py), [`EventPage`](events/models.py)), modèles Django ([`EventStation`](events/models.py), [`StationAssignment`](events/models.py)), [vues HTMX](events/views.py) et [routes](events/urls.py) |
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
- [`EventPage`](events/models.py) — fiche détaillée d'un événement. Le contexte injecte les images, les documents groupés par collection, et un lien d'édition Wagtail admin pour les utilisateurs autorisés. Expose les propriétés `stations_with_counts`, `total_required` et `total_assigned` pour le tableau des postes.

### Gestion des postes (stations)

Chaque événement peut avoir des **postes** ([`EventStation`](events/models.py)) avec un nombre de personnes requises, et des **affectations** ([`StationAssignment`](events/models.py)) de bénévoles à ces postes.

L'interface est accessible via le bouton « Gérer les postes » sur la fiche événement, réservé aux modérateurs. Elle utilise **HTMX** pour offrir une expérience fluide sans rechargement de page :

| Action | Méthode | Route | Vue |
|--------|---------|-------|-----|
| Tableau des postes | GET | `<event_pk>/postes/` | `station_board` |
| Créer un poste | POST | `<event_pk>/postes/creer/` | `station_create` |
| Supprimer un poste | POST | `postes/<station_pk>/supprimer/` | `station_delete` |
| Affecter une personne | POST | `postes/<station_pk>/affecter/` | `assignment_add` |
| Retirer une personne | POST | `affectations/<assignment_pk>/retirer/` | `assignment_remove` |

**Permissions** : toutes les vues sont protégées par `@user_passes_test` — seuls les superusers et les membres du groupe Wagtail `Moderators` y ont accès.

### Hiérarchie des pages

```
HomePage
  └── EventIndexPage
        └── EventPage (pas de sous-pages)
```

Les règles `parent_page_types` et `subpage_types` sont appliquées sur chaque modèle.

### Modèles Django (hors Wagtail Page)

```
EventStation (FK → EventPage)
  └── StationAssignment (FK → EventStation)
```

Suppression en cascade : supprimer un événement supprime ses postes et affectations ; supprimer un poste supprime ses affectations.

### Front-end

- **Tailwind CSS 4** compilé via `@tailwindcss/cli`.
- Source : [`project/static/src/input.css`](project/static/src/input.css) → compilé vers `project/static/css/output.css`.
- Chargé dans [`base.html`](project/templates/base.html) via `{% static 'css/output.css' %}`.
- Palette personnalisée **blason** (bleu azur) définie dans `input.css`.
- **HTMX 2** chargé via CDN dans le template `base.html` pour les interactions dynamiques (ajout/suppression de postes et affectations).

## 🛠️ Développement

```sh
# Terminal 1 — Tailwind (watch)
npm run dev

# Terminal 2 — Django
python manage.py runserver
```

Admin Wagtail : [http://localhost:8000/admin/](http://localhost:8000/admin/)

## ✅ Tests

72 tests couvrent l'ensemble de l'app `events`. Les docstrings suivent le format **Gherkin** (Given / When / Then).

| Fichier | Ce qui est testé |
|---------|-----------------|
| [`core/tests.py`](core/tests.py) | `CustomDocument` : `__str__`, collection par défaut, assignation à une collection personnalisée |
| [`events/tests.py`](events/tests.py) | Hiérarchie des pages · Rendu de l'index et pagination · Accès via `PageViewRestriction` · Visibilité du lien « Voir détails » · Documents par collection · Propriétés `EventPage` (totaux, stations) · Modèles `EventStation` / `StationAssignment` (str, ordering, cascade) · Vues stations (permissions, CRUD, HTMX partials) |

Deux mixins partagés construisent le contexte de test :
- [`EventPageTreeMixin`](events/tests.py) — arbre de pages (root → index → event) ;
- [`StationViewMixin`](events/tests.py) — utilisateurs (superuser, modérateur groupe, lambda).

```sh
python manage.py test
```