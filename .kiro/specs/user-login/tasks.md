# Implementation Plan: user-login

## Overview

El código de producción del login ya existe y está completo (`schemas/user_schema.py`, `services/auth_service.py`, `repositories/user_repository.py`, `controllers/auth_controller.py`). Las tareas se enfocan en tres áreas:

1. **Infraestructura de tests** — instalar dependencias, extender `tests/conftest.py` (reutilizando fixtures del spec `user-registration` si ya existen) y crear helpers de Hypothesis específicos para el flujo de login.
2. **Suite de tests** — property-based tests (Hypothesis) para las 10 propiedades del diseño y tests de ejemplo para los escenarios específicos definidos en la estrategia de testing.
3. **Mejora opcional de manejo de errores** — añadir error handler global en `app.py` si no existe aún, garantizando que no se devuelvan HTTP 500 para inputs inesperados (Property 10).

---

## Tasks

- [x] 1. Configurar infraestructura de tests
  - [x] 1.1 Instalar y anclar dependencias de test
    - Añadir a `requirements.txt` (o `requirements-dev.txt`): `pytest==8.3.5`, `hypothesis==6.131.15`, `pytest-flask==1.3.0` si no están ya presentes.
    - Verificar que `pytest` descubre tests con `pytest --collect-only` sin errores de importación.
    - _Requirements: —_ (prerequisito técnico)
    - **Files:** `requirements.txt`

  - [x] 1.2 Verificar o extender `tests/conftest.py` con fixtures para login
    - Si `tests/conftest.py` ya existe (del spec `user-registration`), verificar que contiene las fixtures `app`, `client`, `db_session` y `seeded_user`.
    - Si no existen, crearlas: `app` → `create_app("testing")` con `SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"` y `TESTING=True`; `client` → `app.test_client()`; `db_session` → `db.create_all()` / `db.drop_all()`.
    - Añadir fixture `seeded_login_user` que inserte un `User` con `generate_password_hash("secret123")` directamente en la BD, retornando `(user, "secret123")` para que los tests de login dispongan de credenciales conocidas.
    - _Requirements: 1.1, 3.1, 3.2_
    - **Files:** `tests/conftest.py`

  - [x] 1.3 Crear `tests/unit/conftest.py` con estrategias de Hypothesis para login
    - Definir `valid_email_st`: estrategia que genere emails conformes a `^[^@\s]+@[^@\s]+\.[^@\s]+$` usando `st.from_regex` o composición `local@domain.tld`.
    - Definir `invalid_email_st`: `st.text().filter(lambda s: bool(s.strip()) and not EMAIL_REGEX.match(s.strip().lower()))`.
    - Definir `valid_username_st`: `st.text(min_size=3, max_size=80).map(str.strip).filter(lambda s: len(s) >= 3)`.
    - Definir `short_username_st`: `st.text(max_size=2)` (incluye cadena vacía).
    - Definir `nonempty_password_st`: `st.text(min_size=1, max_size=128)`.
    - Si el archivo ya existe del spec `user-registration`, añadir únicamente las estrategias que falten.
    - _Requirements: —_ (prerequisito técnico)
    - **Files:** `tests/unit/conftest.py`

- [x] 2. Property tests para `UserValidator` — propiedades 1 a 5
  - [x] 2.1 Crear `tests/unit/test_user_validator_login.py` con clase base
    - Importar `UserValidator` desde `schemas.user_schema`.
    - Importar `EMAIL_REGEX` desde `schemas.user_schema` (o redefinirlo localmente con el mismo patrón si no se exporta).
    - Instanciar `validator = UserValidator()` a nivel de módulo.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_
    - **Files:** `tests/unit/test_user_validator_login.py`

  - [-]* 2.2 Escribir property test — Propiedad 1: identificador ausente siempre produce el error correcto
    - **Property 1: Missing identifier always produces the correct error**
    - **Validates: Requirements 2.1**
    - Para cualquier dict que contenga `password` no vacío pero ni `email` ni `username` no vacíos, `validate_login` debe lanzar `ValueError("Debes proporcionar un correo electrónico o nombre de usuario.")`.
    - `@settings(max_examples=100)` — comentario: `# Feature: user-login, Property 1: missing identifier always produces the correct error`
    - **Files:** `tests/unit/test_user_validator_login.py`

  - [-]* 2.3 Escribir property test — Propiedad 2: email con formato inválido siempre es rechazado
    - **Property 2: Invalid email format is always rejected**
    - **Validates: Requirements 2.2**
    - Para cualquier string que no coincida con `^[^@\s]+@[^@\s]+\.[^@\s]+$` (después de strip + lowercase), junto con `password` no vacío, `validate_login` debe lanzar `ValueError("El correo electrónico no es válido.")`.
    - `@settings(max_examples=100)` — comentario: `# Feature: user-login, Property 2: invalid email format is always rejected`
    - **Files:** `tests/unit/test_user_validator_login.py`

  - [-]* 2.4 Escribir property test — Propiedad 3: username corto siempre es rechazado
    - **Property 3: Short username is always rejected**
    - **Validates: Requirements 2.3**
    - Para cualquier string cuyo stripped length sea < 3, junto con `password` no vacío y sin campo `email`, `validate_login` debe lanzar `ValueError("El nombre de usuario debe tener al menos 3 caracteres.")`.
    - `@settings(max_examples=100)` — comentario: `# Feature: user-login, Property 3: short username is always rejected`
    - **Files:** `tests/unit/test_user_validator_login.py`

  - [-]* 2.5 Escribir property test — Propiedad 4: password ausente o vacía siempre es rechazada
    - **Property 4: Empty or absent password is always rejected**
    - **Validates: Requirements 2.4**
    - Para cualquier dict que contenga un identificador válido (email conforme o username de 3+ chars stripped) pero con `password` ausente, `None` o cadena vacía, `validate_login` debe lanzar `ValueError("La contraseña es requerida.")`.
    - `@settings(max_examples=100)` — comentario: `# Feature: user-login, Property 4: empty or absent password is always rejected`
    - **Files:** `tests/unit/test_user_validator_login.py`

  - [-]* 2.6 Escribir property test — Propiedad 5: normalización de entrada aplicada consistentemente
    - **Property 5: Input normalization is applied consistently**
    - **Validates: Requirements 2.6**
    - Para cualquier email válido (incluyendo espacios extremos o mayúsculas), `validate_login` debe retornar `LoginInput` con `email == raw.strip().lower()` y `username is None`.
    - Para cualquier username válido (incluyendo espacios extremos), `validate_login` debe retornar `LoginInput` con `username == raw.strip()` y `email is None`.
    - `@settings(max_examples=100)` — comentario: `# Feature: user-login, Property 5: input normalization is applied consistently`
    - **Files:** `tests/unit/test_user_validator_login.py`

- [~] 3. Checkpoint — Validar property tests del validador
  - Ejecutar `pytest tests/unit/test_user_validator_login.py -v` y verificar que todos los tests pasan. Consultar al usuario si surgen dudas.

- [x] 4. Property tests para `AuthService` — propiedades 6 y 7
  - [x] 4.1 Crear `tests/unit/test_auth_service_login.py` con repositorios mock
    - Definir `RepoNone`: repositorio stub cuyo `find_by_email` y `find_by_username` siempre retornan `None`.
    - Definir `RepoWrongHash`: repositorio stub que retorna un `User` con `password_hash = generate_password_hash("different_" + password)`.
    - Definir `RepoByField`: repositorio stub configurable que retorna un `User` solo desde `find_by_email` o solo desde `find_by_username` según el campo activo, registrando qué método fue llamado.
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3_
    - **Files:** `tests/unit/test_auth_service_login.py`

  - [~]* 4.2 Escribir property test — Propiedad 6: lookup enrutado al método correcto del repositorio
    - **Property 6: Lookup is routed to the correct repository method**
    - **Validates: Requirements 3.1, 3.2**
    - Para cualquier `LoginInput` con `email` no-`None`, `AuthService.login` debe invocar `find_by_email` con ese valor y nunca `find_by_username`.
    - Para cualquier `LoginInput` con `email=None` y `username` no-`None`, `AuthService.login` debe invocar `find_by_username` y nunca `find_by_email`.
    - Usar `RepoByField` para registrar las llamadas.
    - `@settings(max_examples=100)` — comentario: `# Feature: user-login, Property 6: lookup is routed to the correct repository method`
    - **Files:** `tests/unit/test_auth_service_login.py`

  - [~]* 4.3 Escribir property test — Propiedad 7: fallo de credenciales siempre produce el mismo mensaje
    - **Property 7: Credential failure is always reported with the same message, preventing account enumeration**
    - **Validates: Requirements 3.3, 4.2, 4.3**
    - Para cualquier `LoginInput`, si `AuthService.login` lanza `ValueError` (cuenta inexistente vía `RepoNone` o contraseña incorrecta vía `RepoWrongHash`), el mensaje debe ser byte a byte `"Credenciales incorrectas."` en ambos casos.
    - `@settings(max_examples=100)` — comentario: `# Feature: user-login, Property 7: credential failure prevents account enumeration`
    - **Files:** `tests/unit/test_auth_service_login.py`

- [~] 5. Checkpoint — Validar property tests del servicio
  - Ejecutar `pytest tests/unit/test_auth_service_login.py -v` y verificar que todos los tests pasan. Consultar al usuario si surgen dudas.

- [x] 6. Property tests y unit tests para `AuthController` — propiedades 8 a 10
  - [x] 6.1 Crear `tests/unit/test_auth_controller_login.py` con Flask test client y mocks
    - Importar fixture `client` de `tests/conftest.py`.
    - Definir helper `post_login(client, payload)` → `client.post("/auth/login", json=payload)`.
    - _Requirements: 1.1, 5.1, 5.3, 5.4, 6.1, 6.2, 6.3_
    - **Files:** `tests/unit/test_auth_controller_login.py`

  - [~]* 6.2 Escribir property test — Propiedad 8: JWT identity es siempre str(user.id)
    - **Property 8: JWT identity is always the string representation of the user ID**
    - **Validates: Requirements 5.1**
    - Para cualquier `User` con un `id` entero positivo, cuando `AuthService.login` retorna ese usuario, `AuthController` debe llamar a `create_access_token` con `identity == str(user.id)`.
    - Mockear `AuthService.login` con `unittest.mock.patch` para retornar un `User` con id generado por Hypothesis.
    - `@settings(max_examples=100)` — comentario: `# Feature: user-login, Property 8: JWT identity is always str(user.id)`
    - **Files:** `tests/unit/test_auth_controller_login.py`

  - [~]* 6.3 Escribir property test — Propiedad 9: respuesta exitosa contiene campos requeridos y no expone campos sensibles
    - **Property 9: Success response contains all required fields and no sensitive fields**
    - **Validates: Requirements 5.3, 5.4, 7.2**
    - Para cualquier `User` con `id`, `username` y `email` válidos, la respuesta HTTP de `AuthController` debe: tener status 200; contener `message`, `id`, `username`, `email`, `access_token`; tener `id == user.id`, `username == user.username`, `email == user.email`; y **no** contener las claves `password` ni `password_hash`.
    - Mockear `AuthService.login` para retornar el `User` generado; mockear `create_access_token` para retornar `"fake.token"`.
    - `@settings(max_examples=100)` — comentario: `# Feature: user-login, Property 9: success response contains required fields and no sensitive fields`
    - **Files:** `tests/unit/test_auth_controller_login.py`

  - [~]* 6.4 Escribir property test — Propiedad 10: ningún input JSON parseable produce HTTP 500
    - **Property 10: No HTTP 500 responses for any JSON-parseable input**
    - **Validates: Requirements 6.3**
    - Para cualquier dict JSON serializable (incluyendo objetos vacíos, campos incorrectos, tipos erróneos, campos extra), `POST /auth/login` nunca debe retornar status 500.
    - Usar `st.dictionaries(keys=st.text(max_size=20), values=st.one_of(st.text(), st.integers(), st.none(), st.booleans()), max_size=5)`.
    - `@settings(max_examples=200)` — comentario: `# Feature: user-login, Property 10: no HTTP 500 for any JSON-parseable input`
    - **Files:** `tests/unit/test_auth_controller_login.py`

- [ ] 7. Tests de ejemplo (unit tests) para flujos específicos del controller
  - [~] 7.1 Escribir tests de ejemplo en `tests/unit/test_auth_controller_login.py`
    - Estos tests complementan los property tests con escenarios concretos:
      - Email válido + contraseña correcta → HTTP 200, todos los campos requeridos presentes, sin `password_hash` (cubre Req 5.3, 5.4).
      - Username válido + contraseña correcta → HTTP 200, `username` coincide (cubre Req 1.3, 5.3).
      - Email válido + contraseña incorrecta → HTTP 401, `{"error": "Credenciales incorrectas."}` (cubre Req 6.1).
      - Email inexistente + cualquier contraseña → HTTP 401, mismo mensaje de error (cubre Req 3.3, 4.3).
      - Body vacío `{}` → HTTP 400 (cubre Req 1.2, 2.1).
      - Body ausente o no-JSON (`content_type="text/plain"`) → HTTP 400 (cubre Req 1.2).
      - `create_access_token` llamado con `str(user.id)` (mockear el servicio, verificar la llamada con `assert_called_once_with`) (cubre Req 5.1).
    - Usar fixture `seeded_login_user` de `tests/conftest.py` para los tests end-to-end.
    - _Requirements: 1.2, 1.3, 2.1, 3.3, 4.3, 5.1, 5.3, 5.4, 6.1_
    - **Files:** `tests/unit/test_auth_controller_login.py`

- [~] 8. Checkpoint — Validar suite completa del controller
  - Ejecutar `pytest tests/unit/test_auth_controller_login.py -v` y verificar que todos los tests pasan. Consultar al usuario si surgen dudas.

- [x] 9. Añadir error handler global en `app.py` (si no existe)
  - [x] 9.1 Registrar `@app.errorhandler(Exception)` en la función `create_app`
    - Verificar si `app.py` ya tiene un handler de excepción genérico; si no existe, añadirlo.
    - El handler debe re-lanzar `HTTPException` para que Flask las maneje normalmente y retornar `jsonify({"error": "Error interno del servidor."})` con status 500 para cualquier otra excepción.
    - Este handler garantiza que Property 10 se cumpla incluso ante errores inesperados en capas inferiores.
    - _Requirements: 6.3_
    - **Files:** `app.py`

  - [~]* 9.2 Escribir test de ejemplo para el handler global de 500
    - En `tests/unit/test_auth_controller_login.py`, usar `unittest.mock.patch` para que `UserRepository.find_by_email` lance `Exception("db error")`.
    - Verificar que `POST /auth/login` retorna HTTP 500 con `{"error": "Error interno del servidor."}` y sin stack trace en el cuerpo.
    - _Requirements: 6.3_
    - **Files:** `tests/unit/test_auth_controller_login.py`

- [ ] 10. Verificar que `smoke_test_login.py` sigue pasando
  - [~] 10.1 Ejecutar `smoke_test_login.py` como verificación de capa de integración
    - Ejecutar `python smoke_test_login.py` desde la raíz del proyecto.
    - Verificar que los 4 escenarios definidos en el script pasan: login con email, login con username, contraseña incorrecta, sin identificador.
    - Si algún escenario falla tras los cambios en `app.py` (tarea 9), corregir el handler de forma que no interfiera con las respuestas de error esperadas.
    - _Requirements: 1.1, 1.3, 4.2, 6.1, 6.2_
    - **Files:** `smoke_test_login.py` (solo lectura/verificación; no modificar salvo corrección de ruta de importación)

- [~] 11. Checkpoint final — Verificar cobertura y consistencia
  - Ejecutar `pytest tests/ -v --tb=short` y confirmar que todos los tests pasan.
  - Ejecutar `python smoke_test_login.py` y confirmar que los 4 escenarios pasan.
  - Revisar que cada requisito del documento `requirements.md` tiene al menos un test que lo cubra.
  - Consultar al usuario si surgen dudas antes de cerrar la feature.

---

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido; los property tests son el principal mecanismo de verificación de correctitud según el diseño.
- El código de producción ya está completo; ninguna tarea modifica `schemas/user_schema.py`, `services/auth_service.py`, `repositories/user_repository.py` ni `controllers/auth_controller.py` salvo el error handler en `app.py` (tarea 9.1).
- Los property tests deben ejecutarse con `@settings(max_examples=100)` (200 para Property 10) y llevar el comentario de trazabilidad `# Feature: user-login, Property N: <resumen>`.
- Si `tests/conftest.py` ya fue creado por el spec `user-registration`, solo añadir la fixture `seeded_login_user`; no duplicar `app`, `client` ni `db_session`.
- Las estrategias de Hypothesis en `tests/unit/conftest.py` son reutilizables; si ya existen del spec `user-registration`, solo añadir las específicas de login (`invalid_email_st`, `short_username_st`, `nonempty_password_st`).
- `smoke_test_login.py` actúa como test de integración de capa ya existente y no debe ser modificado, solo ejecutado.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1", "4.1", "6.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.4", "2.5", "2.6", "4.2", "4.3", "9.1"] },
    { "id": 4, "tasks": ["6.2", "6.3", "6.4", "7.1"] },
    { "id": 5, "tasks": ["9.2", "10.1"] }
  ]
}
```
