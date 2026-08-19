# Ejercicio Kiro — API REST de Autenticación con Flask

API REST construida con Flask que implementa registro e inicio de sesión de usuarios con autenticación basada en JWT (JSON Web Tokens).

## ¿Qué hace?

- Registra nuevos usuarios con validación de datos (username, email, contraseña)
- Autentica usuarios por correo electrónico **o** nombre de usuario + contraseña
- Devuelve un JWT de acceso válido por 1 hora al iniciar sesión
- Expone endpoints de salud (`/health`) para monitoreo

## Stack

| Capa | Tecnología |
|---|---|
| Framework | Flask |
| ORM | Flask-SQLAlchemy |
| Migraciones | Flask-Migrate (Alembic) |
| Autenticación | Flask-JWT-Extended |
| Base de datos | SQLite (desarrollo) / PostgreSQL (producción) |
| Validación de passwords | Werkzeug |

## Estructura del proyecto

```
├── app.py                  # Factory de la aplicación Flask
├── config.py               # Configuraciones por entorno
├── extensions.py           # Instancias de db, migrate, jwt
├── db.py                   # Script de creación de base de datos PostgreSQL
├── models/
│   └── user.py             # Modelo User (id, username, email, password_hash)
├── controllers/
│   └── auth_controller.py  # Endpoints de registro y login
├── services/
│   └── auth_service.py     # Lógica de negocio de autenticación
├── repositories/
│   └── user_repository.py  # Acceso a datos del usuario
├── schemas/
│   └── user_schema.py      # Validación y dataclasses de entrada
├── smoke_test_login.py     # Tests funcionales del endpoint de login
└── requirements.txt        # Dependencias del proyecto
```

## Instalación y puesta en marcha

### 1. Crear y activar entorno virtual

```powershell
python -m venv MyEnt
.\MyEnt\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```powershell
pip install flask flask-sqlalchemy flask-migrate flask-jwt-extended werkzeug
```

### 3. Levantar el servidor

```powershell
python app.py
```

El servidor queda disponible en `http://127.0.0.1:5000`.

## Endpoints

### `POST /auth/register` — Registrar usuario

**Body JSON:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "secret123"
}
```

**Respuesta exitosa (201):**
```json
{
  "message": "Usuario registrado.",
  "id": 1,
  "username": "johndoe"
}
```

---

### `POST /auth/login` — Iniciar sesión

Acepta **email o username** como identificador.

**Body JSON (con email):**
```json
{
  "email": "john@example.com",
  "password": "secret123"
}
```

**Body JSON (con username):**
```json
{
  "username": "johndoe",
  "password": "secret123"
}
```

**Respuesta exitosa (200):**
```json
{
  "message": "Login exitoso.",
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "access_token": "eyJ..."
}
```

**Errores posibles:**

| Código | Motivo |
|--------|--------|
| 400 | Datos de entrada inválidos o faltantes |
| 401 | Credenciales incorrectas |

---

### `GET /health` — Estado del servidor

```json
{ "status": "ok" }
```

## Validaciones

- `username`: mínimo 3 caracteres
- `email`: formato válido (contiene `@` y dominio)
- `password`: mínimo 6 caracteres
- El `password_hash` nunca se expone en ninguna respuesta

## Variables de entorno

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `DATABASE_URL` | URL de conexión a la base de datos | `sqlite:///app.db` |
| `JWT_SECRET_KEY` | Clave secreta para firmar los JWT | `change-me-in-production` |
| `FLASK_ENV` | Entorno de ejecución (`development`, `production`) | `development` |

> **Importante:** Cambia `JWT_SECRET_KEY` por una cadena aleatoria de al menos 32 caracteres antes de desplegar a producción.

## Ejecutar los tests

```powershell
.\MyEnt\Scripts\Activate.ps1
python smoke_test_login.py
```

Los tests verifican los 4 escenarios principales del login sin necesitar un servidor activo ni datos en la base de datos real (usan SQLite en memoria).

```
Scenario 1: Login with email + correct password    ✓
Scenario 2: Login with username + correct password ✓
Scenario 3: Correct email, wrong password          ✓
Scenario 4: No identifier provided                 ✓
Results: 17/17 checks passed
```
