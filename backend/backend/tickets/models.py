from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Area(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Sucursal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class Tecnico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)

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

    def save(self, *args, **kwargs):
        # Asignar técnico automáticamente
        if not self.tecnico:
            self.tecnico = Tecnico.objects.filter(area=self.sucursal.area).first()

        # Calcular tiempo límite
        if self.fecha_inicio and not self.fecha_limite:
            if self.prioridad == 'A':
                self.fecha_limite = self.fecha_inicio + timedelta(hours=2)
            elif self.prioridad == 'B':
                self.fecha_limite = self.fecha_inicio + timedelta(hours=5)
            else:
                self.fecha_limite = self.fecha_inicio + timedelta(hours=24)

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
