from rest_framework.permissions import BasePermission


class IsSuperUserOrAdminType(BasePermission):
    """
    Allows access only to Django superuser or app-level admin user_type.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.user_type == "admin")
        )


class IsAdminForWriteElseReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.is_superuser or request.user.user_type == "admin"


class IsOwnerOrAdminObject(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.user_type == "admin":
            return True
        obj_user = getattr(obj, "user", None)
        return obj_user == user
