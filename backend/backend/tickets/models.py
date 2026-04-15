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

    prioridad = models.CharField(max_length=1, choices=PRIORIDAD_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    tecnico = models.ForeignKey(Tecnico, on_delete=models.SET_NULL, null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField()

    comentario_tecnico = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Asignar técnico automáticamente
        if not self.tecnico:
            self.tecnico = Tecnico.objects.filter(area=self.sucursal.area).first()

        # Calcular tiempo límite
        if not self.fecha_limite:
            ahora = timezone.now()

            if self.prioridad == 'A':
                self.fecha_limite = ahora + timedelta(hours=2)
            elif self.prioridad == 'B':
                self.fecha_limite = ahora + timedelta(hours=5)
            else:
                self.fecha_limite = ahora + timedelta(hours=24)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo
     