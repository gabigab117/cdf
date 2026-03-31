def is_moderator(user):
    """Vérifie que l'utilisateur est modérateur Wagtail ou superuser."""
    return user.is_active and (user.is_superuser or user.groups.filter(name="Moderators").exists())


def is_moderator_context(request):
    """Context processor : injecte `is_moderator` dans tous les templates."""
    if hasattr(request, "user") and request.user.is_authenticated:
        return {"is_moderator": is_moderator(request.user)}
    return {"is_moderator": False}
