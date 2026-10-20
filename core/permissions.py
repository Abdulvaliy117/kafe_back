from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """Чтение — всем, запись — только персоналу (is_staff).

    Админка Next.js логинится тем же логином/паролем, что и /admin/,
    получает токен и шлёт его в заголовке Authorization: Token xxx.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)
