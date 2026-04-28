from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


def usuario_es_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or user.is_staff or user.username == 'admin')
    )


def usuario_es_tecnico(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.groups.filter(name='Tecnico').exists()
        and not usuario_es_admin(user)
    )


def usuario_es_consultor(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.groups.filter(name='Consultor').exists()
        and not usuario_es_admin(user)
    )


class Area(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Zona'
        verbose_name_plural = 'Zonas'

    def __str__(self):
        return self.nombre


class Sucursal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, verbose_name='zona')

    def __str__(self):
        return self.nombre


class Tecnico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    area = models.OneToOneField(Area, on_delete=models.CASCADE, verbose_name='zona')

    def __str__(self):
        return self.user.username


class Ticket(models.Model):
    PRIORIDAD_CHOICES = [
        ('A', 'Alta'),
        ('B', 'Media'),
        ('C', 'Baja'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('realizado', 'Realizado'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    equipo = models.CharField(max_length=150, blank=True, null=True)

    prioridad = models.CharField(max_length=1, choices=PRIORIDAD_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    tecnico = models.ForeignKey(Tecnico, on_delete=models.SET_NULL, null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_limite = models.DateTimeField(blank=True, null=True)
    fecha_conclusion = models.DateTimeField(blank=True, null=True)

    comentario_tecnico = models.TextField(blank=True, null=True)
    evidencia_cierre = models.FileField(upload_to='tickets/evidencias/', blank=True, null=True)

    PRIORIDAD_HORAS = {
        'A': 5,
        'B': 15,
        'C': 24,
    }

    @classmethod
    def seleccionar_tecnico_para_sucursal(cls, sucursal):
        if not sucursal:
            return None

        return (
            Tecnico.objects.filter(
                area=sucursal.area,
                user__is_active=True,
                user__groups__name='Tecnico',
            )
            .exclude(user__is_superuser=True)
            .exclude(user__is_staff=True)
            .exclude(user__username='admin')
            .order_by('id')
            .first()
        )

    @property
    def esta_vencido(self):
        return (
            self.estado != 'realizado'
            and self.fecha_limite is not None
            and timezone.now() > self.fecha_limite
        )

    @property
    def estado_alerta(self):
        if self.estado == 'realizado':
            return 'resuelto'

        if self.fecha_limite is None:
            return 'sin_limite'

        ahora = timezone.now()
        if ahora >= self.fecha_limite:
            return 'vencido'

        if ahora >= self.fecha_limite - timedelta(minutes=30):
            return 'por_vencer'

        return 'en_tiempo'

    def calcular_fecha_limite(self):
        if not self.fecha_inicio:
            return None

        horas = self.PRIORIDAD_HORAS.get(self.prioridad)
        if horas is None:
            return None

        return self.fecha_inicio + timedelta(hours=horas)

    def save(self, *args, **kwargs):
        # Asignar el tecnico exclusivo de la zona de la sucursal.
        if not self.tecnico:
            self.tecnico = self.seleccionar_tecnico_para_sucursal(self.sucursal)

        # Calcular tiempo limite
        if self.fecha_inicio and not self.fecha_limite:
            self.fecha_limite = self.calcular_fecha_limite()

        if self.estado == 'realizado' and not self.fecha_conclusion:
            self.fecha_conclusion = timezone.now()
        elif self.estado == 'pendiente':
            self.fecha_conclusion = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


class TicketAlerta(models.Model):
    TIPO_CHOICES = [
        ('por_vencer', 'Por vencer'),
        ('vencido', 'Vencido'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='alertas')
    tecnico = models.ForeignKey(Tecnico, on_delete=models.CASCADE, related_name='alertas')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    mensaje = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    fecha_generada = models.DateTimeField(auto_now_add=True)
    fecha_leida = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['ticket', 'tipo'], name='unique_alerta_por_ticket_y_tipo')
        ]
        ordering = ['leida', '-fecha_generada']

    def marcar_leida(self):
        if not self.leida:
            self.leida = True
            self.fecha_leida = timezone.now()
            self.save(update_fields=['leida', 'fecha_leida'])

    def __str__(self):
        return f'{self.ticket.titulo} - {self.tipo}'
