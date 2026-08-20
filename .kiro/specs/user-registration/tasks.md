# Implementation Plan: user-registration

## Overview

El código de producción del registro ya existe (`schemas/user_schema.py`, `services/auth_service.py`, `repositories/user_repository.py`, `controllers/auth_controller.py`). Las tareas se enfocan en tres áreas:

1. **Infraestructura de tests** — instalar dependencias, crear fixtures y helpers compartidos.
2. **Suite de tests** — property-based tests (Hypothesis) para las 8 propiedades del diseño y tests de ejemplo para flujos de integración.
3. **Mejora de manejo de errores** — añadir el error handler global para HTTP 500 recomendado en el diseño.

---

## Tasks

- [ ] 1. Configurar infraestructura de tests
  - [ ] 1.1 Instalar y anclar dependencias de test
    - Añadir a `requirements.txt` (o `requirements-dev.txt`): `pytest==8.3.5`, `hypothesis==6.131.15`, `pytest-flask==1.3.0`.
    - Verificar que `pytest` descubre tests con `pytest --collect-only` sin errores de importación.
    - _Requirements: —_ (prerequisito técnico)
    - **Files:** `requirements.txt` (o `requirements-dev.txt`)

  - [ ] 1.2 Crear `tests/conftest.py` con fixtures de aplicación y base de datos
    - Definir fixture `app` que llame a `create_app("testing")` con `SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"` y `TESTING = True`.
    - Definir fixture `client` que use `app.test_client()`.
    - Definir fixture `db_session` que ejecute `db.create_all()` antes de cada test y `db.drop_all()` después.
    - Definir fixture `seeded_user` que inserte un `User` directamente en la BD para tests de unicidad.
    - _Requirements: 3.2_
    - **Files:** `tests/conftest.py`

  - [ ] 1.3 Crear `tests/unit/conftest.py` con helpers de Hypothesis
    - Definir estrategia `valid_username_st` (`st.text(min_size=3, max_size=80).map(str.strip).filter(lambda s: len(s) >= 3)`).
    - Definir estrategia `valid_email_st` que componga `local@domain.tld` con `st.from_regex`.
    - Definir estrategia `valid_password_st` (`st.text(min_size=6, max_size=128)`).
    - Definir estrategia `invalid_username_st` (`st.one_of(st.just(""), st.text(max_size=2), st.text(alphabet=" \t\n", min_size=1))`).
    - Definir estrategia `invalid_email_st` filtrando strings que no coincidan con `EMAIL_REGEX`.
    - Definir estrategia `invalid_password_st` (`st.text(max_size=5)`).
    - _Requirements: —_ (prerequisito técnico)
    - **Files:** `tests/unit/conftest.py`

- [ ] 2. Tests de propiedad para `UserValidator`
  - [ ] 2.1 Crear `tests/unit/test_user_validator.py` con clase base y fixture
    - Instanciar `UserValidator()` como fixture o variable de módulo.
    - Importar las estrategias definidas en `tests/unit/conftest.py`.
    - _Requirements: 1.1_
    - **Files:** `tests/unit/test_user_validator.py`

  - [ ]* 2.2 Escribir property test — Propiedad 1: Normalización de entrada válida
    - **Property 1: Normalización de entrada válida**
    - **Validates: Requirements 1.6, 5.1, 5.2**
    - Para cualquier combinación de username válido (con posibles espacios extremos), email válido (con posibles mayúsculas) y password válido (≥ 6 caracteres), `validate_register` debe retornar `RegisterInput` con `username` sin espacios extremos, `email` en minúsculas y `password` sin modificar.
    - `@settings(max_examples=100)` — incluir comentario: `# Feature: user-registration, Property 1: Normalización de entrada válida`
    - **Files:** `tests/unit/test_user_validator.py`

  - [ ]* 2.3 Escribir property test — Propiedad 2: Rechazo de username inválido
    - **Property 2: Rechazo de username inválido**
    - **Validates: Requirements 1.2, 1.3**
    - Para cualquier username que, tras `.strip()`, tenga longitud 0, 1 o 2, `validate_register` debe lanzar `ValueError`.
    - `@settings(max_examples=100)` — incluir comentario: `# Feature: user-registration, Property 2: Rechazo de username inválido`
    - **Files:** `tests/unit/test_user_validator.py`

  - [ ]* 2.4 Escribir property test — Propiedad 3: Rechazo de email inválido
    - **Property 3: Rechazo de email inválido**
    - **Validates: Requirements 1.4**
    - Para cualquier string que no coincida con `^[^@\s]+@[^@\s]+\.[^@\s]+$`, `validate_register` debe lanzar `ValueError`.
    - `@settings(max_examples=100)` — incluir comentario: `# Feature: user-registration, Property 3: Rechazo de email inválido`
    - **Files:** `tests/unit/test_user_validator.py`

  - [ ]* 2.5 Escribir property test — Propiedad 4: Rechazo de password corta
    - **Property 4: Rechazo de password corta**
    - **Validates: Requirements 1.5**
    - Para cualquier password de longitud < 6 (incluyendo cadena vacía), `validate_register` debe lanzar `ValueError`.
    - `@settings(max_examples=100)` — incluir comentario: `# Feature: user-registration, Property 4: Rechazo de password corta`
    - **Files:** `tests/unit/test_user_validator.py`

- [ ] 3. Checkpoint — Validar tests unitarios del validador
  - Ejecutar `pytest tests/unit/test_user_validator.py -v` y verificar que todos los tests pasan. Consultar al usuario si surgen dudas.

- [ ] 4. Tests de propiedad para `AuthService`
  - [ ] 4.1 Crear `tests/unit/test_auth_service.py` con mocks del repositorio
    - Instanciar `AuthService` con un `MagicMock` como repositorio en cada test.
    - Importar `RegisterInput` y las estrategias de `tests/unit/conftest.py`.
    - _Requirements: 2.1, 2.2_
    - **Files:** `tests/unit/test_auth_service.py`

  - [ ]* 4.2 Escribir property test — Propiedad 5: Rechazo por duplicado de email o username
    - **Property 5: Rechazo por duplicado de email o username**
    - **Validates: Requirements 2.1, 2.2**
    - Para cualquier `RegisterInput` válido, si `repo.find_by_email` retorna un `User` existente, `AuthService.register` debe lanzar `ValueError`. Igualmente si `find_by_email` retorna `None` pero `find_by_username` retorna un `User`, debe lanzar `ValueError`.
    - `@settings(max_examples=100)` — incluir comentario: `# Feature: user-registration, Property 5: Rechazo por duplicado de email o username`
    - **Files:** `tests/unit/test_auth_service.py`

  - [ ]* 4.3 Escribir property test — Propiedad 6: Invariante del usuario guardado
    - **Property 6: Invariante del usuario guardado**
    - **Validates: Requirements 3.1, 5.3**
    - Para cualquier `RegisterInput` válido (email y username no duplicados), el `User` que se pasa a `repo.save` debe satisfacer: `user.username == input_data.username`, `user.email == input_data.email`, `user.password_hash != input_data.password`, y `check_password_hash(user.password_hash, input_data.password) == True`.
    - Usar `repo.save = MagicMock(side_effect=lambda u: u)` para capturar el objeto sin persistir.
    - `@settings(max_examples=100)` — incluir comentario: `# Feature: user-registration, Property 6: Invariante del usuario guardado`
    - **Files:** `tests/unit/test_auth_service.py`

- [ ] 5. Tests de integración para `auth_controller` y flujo completo
  - [ ] 5.1 Crear `tests/integration/test_auth_controller.py` con Flask test client
    - Importar fixtures `client` y `db_session` de `tests/conftest.py`.
    - Helper `post_register(client, payload)` que hace `POST /auth/register` con `content_type="application/json"`.
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
    - **Files:** `tests/integration/test_auth_controller.py`

  - [ ]* 5.2 Escribir property test — Propiedad 7: Forma de respuesta HTTP 201 en registro exitoso
    - **Property 7: Forma de la respuesta HTTP en registro exitoso**
    - **Validates: Requirements 4.1**
    - Para cualquier combinación válida y única de username, email y password, `POST /auth/register` debe retornar HTTP 201 con cuerpo JSON que contenga `message`, `id` y `username`, donde `username` coincide con el username enviado.
    - Usar BD SQLite en memoria; generar datos únicos por iteración (p. ej. añadir sufijo con `uuid4()`).
    - `@settings(max_examples=50)` — incluir comentario: `# Feature: user-registration, Property 7: Forma de la respuesta HTTP en registro exitoso`
    - **Files:** `tests/integration/test_auth_controller.py`

  - [ ]* 5.3 Escribir property test — Propiedad 8: Forma de respuesta HTTP 400 en error
    - **Property 8: Forma de la respuesta HTTP en error**
    - **Validates: Requirements 4.2, 4.3**
    - Para cualquier solicitud que provoque `ValueError` en el validador o en el servicio, la respuesta debe tener HTTP 400 y cuerpo JSON con campo `error` no vacío.
    - Cubrir inputs de validación inválidos (username vacío, email malformado, password corta) y unicidad (email/username duplicados).
    - `@settings(max_examples=100)` — incluir comentario: `# Feature: user-registration, Property 8: Forma de la respuesta HTTP en error`
    - **Files:** `tests/integration/test_auth_controller.py`

  - [ ]* 5.4 Escribir tests de ejemplo para flujos específicos
    - Registro exitoso end-to-end con BD SQLite en memoria — verifica que el usuario queda persistido (cubre Req 3.2).
    - Registro con body no-JSON (`content_type="text/plain"`) — debe retornar HTTP 400 con campo `error` (cubre Req 4.4).
    - Re-registro con el mismo email — verifica HTTP 400 y mensaje descriptivo (cubre Req 2.3 flujo completo).
    - Re-registro con el mismo username — verifica HTTP 400 y mensaje descriptivo (cubre Req 2.2 flujo completo).
    - **Files:** `tests/integration/test_auth_controller.py`

- [ ] 6. Tests de integración para `UserRepository`
  - [ ] 6.1 Crear `tests/integration/test_user_repository.py`
    - Usar fixture `db_session` con BD SQLite en memoria.
    - Tests de ejemplo:
      - `save` persiste el usuario y retorna el objeto con `id` asignado (cubre Req 3.2).
      - `find_by_email` retorna el usuario correcto o `None` (cubre Req 2.1).
      - `find_by_username` retorna el usuario correcto o `None` (cubre Req 2.2).
      - `save` propaga `IntegrityError` cuando se inserta un email duplicado directamente (cubre Req 3.3).
    - _Requirements: 2.1, 2.2, 3.2, 3.3_
    - **Files:** `tests/integration/test_user_repository.py`

- [ ] 7. Checkpoint — Validar suite de integración completa
  - Ejecutar `pytest tests/ -v` y verificar que todos los tests pasan. Consultar al usuario si surgen dudas.

- [ ] 8. Añadir error handler global para HTTP 500 en `app.py`
  - [ ] 8.1 Registrar `@app.errorhandler(Exception)` en la función `create_app`
    - El handler debe retornar `jsonify({"error": "Error interno del servidor."})` con código 500.
    - Garantizar que no silencia errores de `werkzeug` (re-lanzar `HTTPException` para que Flask los maneje normalmente).
    - _Requirements: 3.3_ (recomendación de diseño para no exponer trazas al cliente)
    - **Files:** `app.py`

  - [ ]* 8.2 Escribir test de ejemplo para el handler de 500
    - En `tests/integration/test_auth_controller.py`, mockear `UserRepository.save` para que lance `SQLAlchemyError`.
    - Verificar que `POST /auth/register` retorna HTTP 500 con `{"error": "Error interno del servidor."}` y sin traza de stack.
    - _Requirements: 3.3_
    - **Files:** `tests/integration/test_auth_controller.py`

- [ ] 9. Checkpoint final — Verificar cobertura y consistencia
  - Ejecutar `pytest tests/ -v --tb=short` y confirmar que todos los tests pasan.
  - Revisar que cada requisito del documento `requirements.md` tiene al menos un test que lo cubra.
  - Consultar al usuario si surgen dudas antes de cerrar la feature.

---

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido; los tests de propiedad son el mecanismo principal de verificación de correctitud según el diseño.
- El código de producción ya existe; ninguna tarea modifica `schemas/user_schema.py`, `services/auth_service.py`, `repositories/user_repository.py` ni `controllers/auth_controller.py` salvo la tarea 8.1.
- Los property tests deben ejecutarse con `@settings(max_examples=100)` y llevar el comentario de trazabilidad `# Feature: user-registration, Property N: <texto>`.
- Las estrategias de Hypothesis definidas en `tests/unit/conftest.py` son reutilizables por todos los tests unitarios.
- Para los property tests de integración (P7) se recomienda añadir un sufijo único (`uuid4()`) a username y email para evitar colisiones entre iteraciones dentro de la misma base de datos en memoria.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1", "4.1", "5.1", "6.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.4", "2.5", "4.2", "4.3", "8.1"] },
    { "id": 4, "tasks": ["5.2", "5.3", "5.4"] },
    { "id": 5, "tasks": ["8.2"] }
  ]
}
```
