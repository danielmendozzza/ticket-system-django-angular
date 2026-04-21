from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import usuario_es_admin, usuario_es_tecnico


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user

        # 🔥 detectar rol
        if usuario_es_admin(user):
            role = "Admin"
        elif usuario_es_tecnico(user):
            role = "Tecnico"
        elif user.groups.filter(name="Sucursal").exists():
            role = "Sucursal"
        else:
            role = "SinRol"

        data['role'] = role
        data['username'] = user.username

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
