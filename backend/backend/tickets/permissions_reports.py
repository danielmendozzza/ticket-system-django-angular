from rest_framework.permissions import BasePermission


from .models import usuario_es_admin, usuario_es_consultor


class SoloUsuarioAdminReportesPermission(BasePermission):
    message = 'Solo administradores y consultores pueden acceder a los reportes.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (usuario_es_admin(user) or usuario_es_consultor(user)))
