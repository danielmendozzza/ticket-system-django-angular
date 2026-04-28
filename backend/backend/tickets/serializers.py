from django.contrib.auth.models import Group, User
from django.db import transaction
from rest_framework import serializers

from .models import Area, Sucursal, Tecnico, Ticket, usuario_es_tecnico


class TicketSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    tecnico_nombre = serializers.CharField(source='tecnico.user.username', read_only=True)
    area_nombre = serializers.CharField(source='sucursal.area.nombre', read_only=True)
    esta_vencido = serializers.BooleanField(read_only=True)
    estado_alerta = serializers.CharField(read_only=True)
    evidencia_cierre_url = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = (
            'id',
            'titulo',
            'descripcion',
            'equipo',
            'prioridad',
            'estado',
            'sucursal',
            'sucursal_nombre',
            'tecnico',
            'tecnico_nombre',
            'area_nombre',
            'fecha_creacion',
            'fecha_inicio',
            'fecha_limite',
            'fecha_conclusion',
            'comentario_tecnico',
            'evidencia_cierre',
            'evidencia_cierre_url',
            'esta_vencido',
            'estado_alerta',
        )
        read_only_fields = (
            'tecnico',
            'fecha_creacion',
            'fecha_limite',
            'fecha_conclusion',
            'esta_vencido',
            'estado_alerta',
            'sucursal_nombre',
            'tecnico_nombre',
            'area_nombre',
            'evidencia_cierre_url',
        )

    def get_evidencia_cierre_url(self, ticket):
        if not ticket.evidencia_cierre:
            return None

        url = ticket.evidencia_cierre.url
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(url)
        return url

    def validate_evidencia_cierre(self, archivo):
        if not archivo:
            return archivo

        extensiones_permitidas = ('.jpg', '.jpeg', '.png', '.webp')
        nombre = archivo.name.lower()
        if not nombre.endswith(extensiones_permitidas):
            raise serializers.ValidationError('La evidencia debe ser una imagen JPG, PNG o WEBP.')

        content_type = getattr(archivo, 'content_type', '')
        if content_type and not content_type.startswith('image/'):
            raise serializers.ValidationError('La evidencia debe ser un archivo de imagen.')

        limite_mb = 8
        if archivo.size > limite_mb * 1024 * 1024:
            raise serializers.ValidationError(f'La imagen no puede superar {limite_mb} MB.')

        return archivo


class TicketCreateSerializer(TicketSerializer):
    PRIORIDAD_POR_EQUIPO = {
        'exhibidora': 'A',
        'mueble': 'B',
    }

    def validate_equipo(self, equipo):
        equipo_normalizado = (equipo or '').strip().lower()
        if equipo_normalizado not in self.PRIORIDAD_POR_EQUIPO:
            raise serializers.ValidationError('Selecciona Exhibidora o Mueble como equipo.')
        return 'Exhibidora' if equipo_normalizado == 'exhibidora' else 'Mueble'

    def validate(self, attrs):
        attrs = super().validate(attrs)
        equipo = (attrs.get('equipo') or '').strip().lower()
        attrs['prioridad'] = self.PRIORIDAD_POR_EQUIPO.get(equipo, 'B')
        attrs['titulo'] = f'Incidencia en {attrs["equipo"]}'
        return attrs

    class Meta(TicketSerializer.Meta):
        read_only_fields = TicketSerializer.Meta.read_only_fields + ('estado', 'sucursal', 'titulo')


class TicketAdminCreateSerializer(TicketSerializer):
    tecnico = serializers.PrimaryKeyRelatedField(
        queryset=Tecnico.objects.select_related('user', 'area'),
        required=False,
        allow_null=True,
    )

    def validate_sucursal(self, sucursal):
        if sucursal is None:
            raise serializers.ValidationError('Selecciona una sucursal para el ticket.')
        return sucursal

    def validate(self, attrs):
        sucursal = attrs.get('sucursal')
        tecnico = attrs.get('tecnico')

        if sucursal is None:
            raise serializers.ValidationError('Selecciona una sucursal para el ticket.')

        if tecnico is not None:
            if not usuario_es_tecnico(tecnico.user):
                raise serializers.ValidationError('Solo se pueden asignar usuarios con rol Tecnico.')
            if tecnico.area_id != sucursal.area_id:
                raise serializers.ValidationError('El tecnico asignado debe pertenecer a la misma zona de la sucursal.')

        return attrs

    class Meta(TicketSerializer.Meta):
        read_only_fields = (
            'fecha_creacion',
            'fecha_limite',
            'fecha_conclusion',
            'esta_vencido',
            'estado_alerta',
            'estado',
            'sucursal_nombre',
            'tecnico_nombre',
            'area_nombre',
        )


class TicketUpdateSerializer(TicketSerializer):
    class Meta(TicketSerializer.Meta):
        read_only_fields = TicketSerializer.Meta.read_only_fields + (
            'titulo',
            'descripcion',
            'equipo',
            'prioridad',
            'sucursal',
            'fecha_inicio',
        )


class TicketAdminUpdateSerializer(TicketSerializer):
    def validate_tecnico(self, tecnico):
        if tecnico is not None and not usuario_es_tecnico(tecnico.user):
            raise serializers.ValidationError('Solo se pueden asignar usuarios con rol Tecnico.')

        if tecnico is not None and self.instance and tecnico.area_id != self.instance.sucursal.area_id:
            raise serializers.ValidationError('El tecnico asignado debe pertenecer a la misma zona de la sucursal.')

        return tecnico

    def update(self, instance, validated_data):
        prioridad_actualizada = (
            'prioridad' in validated_data and validated_data['prioridad'] != instance.prioridad
        )
        inicio_actualizado = (
            'fecha_inicio' in validated_data and validated_data['fecha_inicio'] != instance.fecha_inicio
        )
        fecha_limite_enviada = validated_data.get('fecha_limite', serializers.empty)
        fecha_limite_sin_cambios = (
            fecha_limite_enviada is serializers.empty
            or fecha_limite_enviada == instance.fecha_limite
        )

        if (prioridad_actualizada or inicio_actualizado) and fecha_limite_sin_cambios:
            validated_data['fecha_limite'] = None

        return super().update(instance, validated_data)

    class Meta(TicketSerializer.Meta):
        read_only_fields = (
            'fecha_creacion',
            'esta_vencido',
            'estado_alerta',
            'sucursal_nombre',
            'tecnico_nombre',
            'area_nombre',
        )


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ('id', 'nombre')

    def validate_nombre(self, nombre):
        queryset = Area.objects.filter(nombre__iexact=nombre.strip())
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('Ya existe una zona con ese nombre.')
        return nombre.strip()


class SucursalSerializer(serializers.ModelSerializer):
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)

    class Meta:
        model = Sucursal
        fields = ('id', 'nombre', 'direccion', 'area', 'area_nombre')


class AdminUserSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()
    area = serializers.SerializerMethodField()
    zona = serializers.SerializerMethodField()
    nombre_sucursal = serializers.SerializerMethodField()
    direccion = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'rol',
            'area',
            'zona',
            'nombre_sucursal',
            'direccion',
        )

    def get_rol(self, user):
        if user.groups.filter(name='Consultor').exists():
            return 'Consultor'
        if user.groups.filter(name='Tecnico').exists():
            return 'Tecnico'
        if user.groups.filter(name='Sucursal').exists():
            return 'Sucursal'
        if user.is_superuser or user.is_staff:
            return 'Admin'
        return 'SinRol'

    def get_area(self, user):
        tecnico = getattr(user, 'tecnico', None)
        if tecnico:
            return tecnico.area_id

        sucursal = getattr(user, 'sucursal', None)
        if sucursal:
            return sucursal.area_id

        return None

    def get_zona(self, user):
        tecnico = getattr(user, 'tecnico', None)
        if tecnico:
            return tecnico.area.nombre

        sucursal = getattr(user, 'sucursal', None)
        if sucursal:
            return sucursal.area.nombre

        return None

    def get_nombre_sucursal(self, user):
        sucursal = getattr(user, 'sucursal', None)
        if sucursal:
            return sucursal.nombre
        return ''

    def get_direccion(self, user):
        sucursal = getattr(user, 'sucursal', None)
        if sucursal:
            return sucursal.direccion or ''
        return ''


class AdminUserWriteSerializer(serializers.Serializer):
    ROLE_CHOICES = (
        ('Tecnico', 'Tecnico'),
        ('Sucursal', 'Sucursal'),
        ('Consultor', 'Consultor'),
    )

    username = serializers.CharField(max_length=150, required=False)
    password = serializers.CharField(write_only=True, min_length=6, required=False, allow_blank=True)
    rol = serializers.ChoiceField(choices=ROLE_CHOICES)
    area = serializers.PrimaryKeyRelatedField(queryset=Area.objects.all(), required=False, allow_null=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    nombre_sucursal = serializers.CharField(max_length=100, required=False, allow_blank=True)
    direccion = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_username(self, username):
        queryset = User.objects.filter(username=username)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('Ya existe un usuario con ese nombre.')
        return username

    def validate(self, attrs):
        rol = attrs['rol']
        area = attrs.get('area')

        if rol in ('Tecnico', 'Sucursal') and area is None:
            raise serializers.ValidationError('Selecciona una zona para el usuario.')

        tecnico_queryset = Tecnico.objects.filter(area=area)
        if self.instance:
            tecnico_queryset = tecnico_queryset.exclude(user=self.instance)

        if rol == 'Tecnico' and tecnico_queryset.exists():
            raise serializers.ValidationError('Esta zona ya tiene un tecnico asignado.')

        if rol == 'Sucursal' and not attrs.get('nombre_sucursal', '').strip():
            attrs['nombre_sucursal'] = attrs.get('username') or getattr(self.instance, 'username', '')

        return attrs

    def to_representation(self, instance):
        return AdminUserSerializer(instance, context=self.context).data


class AdminUserCreateSerializer(AdminUserWriteSerializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)

    @transaction.atomic
    def create(self, validated_data):
        rol = validated_data.pop('rol')
        area = validated_data.pop('area', None)
        password = validated_data.pop('password')
        nombre_sucursal = validated_data.pop('nombre_sucursal', '')
        direccion = validated_data.pop('direccion', '')

        user = User.objects.create_user(password=password, **validated_data)
        group, _ = Group.objects.get_or_create(name=rol)
        user.groups.add(group)

        if rol == 'Tecnico':
            Tecnico.objects.create(user=user, area=area)
        elif rol == 'Sucursal':
            Sucursal.objects.create(
                user=user,
                nombre=nombre_sucursal or user.username,
                direccion=direccion,
                area=area,
            )

        return user


class AdminUserUpdateSerializer(AdminUserWriteSerializer):
    @transaction.atomic
    def update(self, user, validated_data):
        rol = validated_data.pop('rol')
        area = validated_data.pop('area', None)
        password = validated_data.pop('password', '')
        nombre_sucursal = validated_data.pop('nombre_sucursal', '')
        direccion = validated_data.pop('direccion', '')

        for field, value in validated_data.items():
            setattr(user, field, value)

        if password:
            user.set_password(password)

        user.groups.remove(*user.groups.filter(name__in=['Tecnico', 'Sucursal', 'Consultor']))
        group, _ = Group.objects.get_or_create(name=rol)
        user.groups.add(group)
        user.save()

        tecnico = getattr(user, 'tecnico', None)
        sucursal = getattr(user, 'sucursal', None)

        if rol == 'Consultor':
            if tecnico:
                tecnico.delete()
            if sucursal:
                sucursal.user = None
                sucursal.save(update_fields=['user'])

            return user

        if rol == 'Tecnico':
            if sucursal:
                sucursal.user = None
                sucursal.save(update_fields=['user'])

            if tecnico:
                tecnico.area = area
                tecnico.save(update_fields=['area'])
            else:
                Tecnico.objects.create(user=user, area=area)

            return user

        if tecnico:
            tecnico.delete()

        if sucursal:
            sucursal.nombre = nombre_sucursal or user.username
            sucursal.direccion = direccion
            sucursal.area = area
            sucursal.save(update_fields=['nombre', 'direccion', 'area'])
        else:
            Sucursal.objects.create(
                user=user,
                nombre=nombre_sucursal or user.username,
                direccion=direccion,
                area=area,
            )

        return user
