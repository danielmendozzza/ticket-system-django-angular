from django.contrib.auth.models import User
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Area, Sucursal, Ticket, usuario_es_admin, usuario_es_consultor, usuario_es_superadmin, usuario_es_tecnico
from .permissions import TicketPermission
from .serializers import (
    AdminUserCreateSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    AreaSerializer,
    SucursalSerializer,
    TicketAdminCreateSerializer,
    TicketAdminUpdateSerializer,
    TicketCreateSerializer,
    TicketSerializer,
    TicketUpdateSerializer,
)


class AdminOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and usuario_es_admin(request.user))


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related('sucursal', 'sucursal__area', 'tecnico', 'tecnico__user')
    serializer_class = TicketSerializer
    permission_classes = [TicketPermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action == 'create':
            if usuario_es_admin(self.request.user):
                return TicketAdminCreateSerializer
            return TicketCreateSerializer

        if self.action in ('update', 'partial_update'):
            if usuario_es_admin(self.request.user):
                return TicketAdminUpdateSerializer
            return TicketUpdateSerializer

        return TicketSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = self.queryset.all()

        if usuario_es_admin(user):
            return queryset

        if usuario_es_consultor(user):
            return queryset

        # Tecnico que vea solo sus tickets.
        if usuario_es_tecnico(user):
            return queryset.filter(tecnico__user=user)

        if user.groups.filter(name="Sucursal").exists():
            return queryset.filter(sucursal__user=user)

        return Ticket.objects.none()

    def perform_create(self, serializer):
        if usuario_es_admin(self.request.user):
            sucursal = serializer.validated_data.get('sucursal')
            if sucursal is None:
                raise ValidationError('Selecciona una sucursal para el ticket.')

            tecnico = serializer.validated_data.get('tecnico') or Ticket.seleccionar_tecnico_para_sucursal(sucursal)
            if tecnico is None:
                raise ValidationError(
                    'No hay tecnicos activos disponibles para la zona de esta sucursal.'
                )

            serializer.save(tecnico=tecnico)
            return

        sucursal = getattr(self.request.user, 'sucursal', None)
        if sucursal is None:
            raise ValidationError('El usuario autenticado no tiene una sucursal asociada.')

        tecnico = Ticket.seleccionar_tecnico_para_sucursal(sucursal)
        if tecnico is None:
            raise ValidationError(
                'No hay tecnicos activos disponibles para la zona de esta sucursal.'
            )

        serializer.save(sucursal=sucursal, tecnico=tecnico)

    @action(detail=True, methods=['delete'], url_path='borrar-evidencia')
    def borrar_evidencia(self, request, pk=None):
        if not usuario_es_admin(request.user):
            return Response(
                {'detail': 'Solo el administrador puede borrar la evidencia.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        ticket = self.get_object()
        if ticket.evidencia_cierre:
            ticket.evidencia_cierre.delete(save=False)
            ticket.evidencia_cierre = None
            ticket.save(update_fields=['evidencia_cierre'])

        return Response(self.get_serializer(ticket).data)


class AreaViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Area.objects.order_by('nombre')
    serializer_class = AreaSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AdminOnlyPermission()]
        return [IsAuthenticated()]


class SucursalViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Sucursal.objects.select_related('area').order_by('nombre')
    serializer_class = SucursalSerializer
    permission_classes = [AdminOnlyPermission]


class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.prefetch_related('groups').select_related('tecnico__area', 'sucursal__area').order_by('username')
    permission_classes = [AdminOnlyPermission]

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminUserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return AdminUserUpdateSerializer
        return AdminUserSerializer

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        if usuario_es_superadmin(user):
            return Response(
                {'detail': 'El superadmin reservado no se modifica desde este panel.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if usuario_es_admin(user) and not usuario_es_superadmin(request.user):
            return Response(
                {'detail': 'Solo el superadmin puede modificar usuarios administradores.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        if user.pk == request.user.pk:
            return Response(
                {'detail': 'No podes borrar el usuario con el que estas conectado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if usuario_es_superadmin(user):
            return Response(
                {'detail': 'El superadmin reservado no se puede borrar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if usuario_es_admin(user) and not usuario_es_superadmin(request.user):
            return Response(
                {'detail': 'Solo el superadmin puede borrar usuarios administradores.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        sucursal = getattr(user, 'sucursal', None)
        if sucursal:
            sucursal.user = None
            sucursal.save(update_fields=['user'])

        return super().destroy(request, *args, **kwargs)
