from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .alert_views import TicketAlertaViewSet
from .report_views import ReporteResumenAPIView
from .views import TicketViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet)
router.register(r'alertas', TicketAlertaViewSet, basename='alertas')

urlpatterns = [
    path('reportes/resumen/', ReporteResumenAPIView.as_view(), name='reportes-resumen'),
    path('', include(router.urls)),
]
