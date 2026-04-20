from rest_framework.permissions import BasePermission, SAFE_METHODS


class TicketPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.username == 'admin':
            return True

        if request.method in SAFE_METHODS:
            return True

        if request.method == 'POST':
            return request.user.groups.filter(name='Sucursal').exists()

        return request.user.groups.filter(name='Tecnico').exists()

    def has_object_permission(self, request, view, obj):
        if request.user.username == 'admin':
            return True

        if request.method in SAFE_METHODS:
            if request.user.groups.filter(name='Tecnico').exists():
                return obj.tecnico and obj.tecnico.user_id == request.user.id

            if request.user.groups.filter(name='Sucursal').exists():
                return obj.sucursal and obj.sucursal.user_id == request.user.id

            return False

        if request.user.groups.filter(name='Tecnico').exists():
            return obj.tecnico and obj.tecnico.user_id == request.user.id

        return False
