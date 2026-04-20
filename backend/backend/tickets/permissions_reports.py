from rest_framework.permissions import BasePermission


class SoloUsuarioAdminReportesPermission(BasePermission):
    message = 'Solo el usuario admin puede acceder a los reportes.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.username == 'admin')
