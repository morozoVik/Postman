from rest_framework import permissions


class IsModerator(permissions.BasePermission):
    """Проверяет, является ли пользователь модератором"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name="Модераторы").exists()

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwner(permissions.BasePermission):
    """Проверяет, является ли пользователь владельцем объекта"""

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if hasattr(obj, "owner") and obj.owner:
            return obj.owner == request.user
        elif hasattr(obj, "user") and obj.user:
            return obj.user == request.user
        elif hasattr(obj, "author") and obj.author:
            return obj.author == request.user

        return True


class IsAdminOrModerator(permissions.BasePermission):
    """Проверяет, является ли пользователь админом или модератором"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff
            or request.user.groups.filter(name="Модераторы").exists()
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
