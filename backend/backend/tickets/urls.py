from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .alert_views import TicketAlertaViewSet
from .report_views import ReporteResumenAPIView, ReporteTicketsExcelAPIView
from .views import AdminUserViewSet, AreaViewSet, SucursalViewSet, TicketViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet)
router.register(r'alertas', TicketAlertaViewSet, basename='alertas')
router.register(r'areas', AreaViewSet, basename='areas')
router.register(r'sucursales', SucursalViewSet, basename='sucursales')
router.register(r'admin/usuarios', AdminUserViewSet, basename='admin-usuarios')

urlpatterns = [
    path('reportes/resumen/', ReporteResumenAPIView.as_view(), name='reportes-resumen'),
    path('reportes/tickets-excel/', ReporteTicketsExcelAPIView.as_view(), name='reportes-tickets-excel'),
    path('', include(router.urls)),
]
