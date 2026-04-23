# Produccion - Guia Practica

Este documento te deja el sistema listo para una prueba de produccion en otra notebook.

## 1) Requisitos en la notebook servidora

- Docker Desktop instalado y funcionando.
- Puerto `80` habilitado en firewall local.
- Git instalado.

## 2) Clonar y preparar

```powershell
git clone <TU_REPO_URL>
cd sistema
copy .env.prod.example .env.prod
```

Edita `.env.prod` y cambia como minimo:

- `POSTGRES_PASSWORD`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS` (agrega IP real de la notebook servidora)
- `DJANGO_CORS_ALLOWED_ORIGINS` (si usaras dominio/IP publica)

## 3) Levantar produccion local

```powershell
docker compose -f docker-compose.prod.yml up -d --build
```

Ver estado:

```powershell
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

## 4) Crear usuarios de prueba por roles

El proyecto ya crea `admin` por migracion:

- usuario: `admin`
- password: `admin-2026`

Ahora crea tecnico/sucursal/consultor demo:

```powershell
docker compose -f docker-compose.prod.yml exec backend python manage.py seed_demo_access
```

Credenciales demo:

- `tecnico_demo / tecnico-2026`
- `sucursal_demo / sucursal-2026`
- `consultor_demo / consultor-2026`

## 5) Acceder desde otra notebook en la red

En la notebook servidora, obten su IP LAN:

```powershell
ipconfig
```

Busca IPv4, por ejemplo `192.168.1.50`.

Desde esta notebook (cliente), entra a:

- `http://192.168.1.50`

Si no abre:

- revisa firewall Windows (entrada TCP 80)
- confirma que `frontend` este `Up`

## 6) Donde vive la base de datos y si se crea nueva

- Postgres corre en el servicio `db`.
- Datos persistentes en el volumen `postgres_data`.
- Se crea una base nueva en el primer arranque (segun `POSTGRES_DB`).
- Si borras volumen (`docker volume rm`), se pierde esa base.

## 7) Backup y restore basicos

Backup:

```powershell
docker compose -f docker-compose.prod.yml exec -T db sh -lc 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
```

Restore:

```powershell
Get-Content .\backup.sql | docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## 8) Capacidad de la base de datos

No hay limite duro configurado por la app. La capacidad depende de:

- espacio en disco de la notebook/servidor
- RAM/CPU disponibles
- crecimiento de tickets y adjuntos (si se agregan en el futuro)

Para piloto, normalmente alcanza de sobra. En produccion formal, define:

- disco minimo y alertas de uso
- backup diario con retencion
- monitoreo de salud de contenedores

## 9) Comandos utiles de operacion

Actualizar despues de `git pull`:

```powershell
docker compose -f docker-compose.prod.yml up -d --build
```

Parar:

```powershell
docker compose -f docker-compose.prod.yml down
```

Parar sin borrar datos:

- `down` conserva el volumen por defecto.

Parar y borrar datos:

```powershell
docker compose -f docker-compose.prod.yml down -v
```

## 10) Recomendaciones de seguridad antes de abrir internet

- Cambiar password de `admin` inmediatamente.
- No exponer puerto `5432` a internet.
- Usar HTTPS (Nginx/Caddy + certificado).
- Rotar secretos en `.env.prod`.
