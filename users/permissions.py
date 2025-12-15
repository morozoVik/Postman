from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()

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

        if isinstance(obj, User):
            return obj == request.user

        if hasattr(obj, "owner") and obj.owner:
            return obj.owner == request.user
        elif hasattr(obj, "user") and obj.user:
            return obj.user == request.user
        elif hasattr(obj, "author") and obj.author:
            return obj.author == request.user

        return False


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


class IsOwnerOrModeratorOrAdmin(permissions.BasePermission):
    """Разрешает доступ владельцам, модераторам и админам"""

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.is_staff or request.user.groups.filter(name='Модераторы').exists():
            return True

        if hasattr(obj, 'owner') and obj.owner:
            return obj.owner == request.user
        return False


class IsNotModerator(permissions.BasePermission):
    """Проверяет, что пользователь НЕ модератор"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return not request.user.groups.filter(name='Модераторы').exists()


class CanViewOwnObjects(permissions.BasePermission):
    """Разрешает просматривать только свои объекты (для не-модераторов)"""

    def has_permission(self, request, view):
        return request.user.is_authenticated