from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import usuario_es_admin, usuario_es_tecnico


class TicketPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if usuario_es_admin(request.user):
            return True

        if request.method in SAFE_METHODS:
            return True

        if request.method == 'POST':
            return request.user.groups.filter(name='Sucursal').exists()

        return usuario_es_tecnico(request.user)

    def has_object_permission(self, request, view, obj):
        if usuario_es_admin(request.user):
            return True

        if request.method in SAFE_METHODS:
            if usuario_es_tecnico(request.user):
                return obj.tecnico and obj.tecnico.user_id == request.user.id

            if request.user.groups.filter(name='Sucursal').exists():
                return obj.sucursal and obj.sucursal.user_id == request.user.id

            return False

        if usuario_es_tecnico(request.user):
            return obj.tecnico and obj.tecnico.user_id == request.user.id

        return False
