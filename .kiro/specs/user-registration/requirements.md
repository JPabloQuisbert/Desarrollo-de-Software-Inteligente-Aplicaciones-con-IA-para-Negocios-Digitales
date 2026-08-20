# Requirements Document

## Introduction

Esta feature cubre el registro de nuevos usuarios en la API REST construida con Flask. El endpoint `POST /auth/register` permite a cualquier persona crear una cuenta proporcionando un nombre de usuario, correo electrónico y contraseña. El sistema valida los datos de entrada, verifica unicidad de usuario y correo, almacena la contraseña de forma segura mediante hash, y devuelve la confirmación de la cuenta creada.

## Glossary

- **API**: La aplicación Flask que expone los endpoints REST.
- **Validator**: El componente `UserValidator` definido en `schemas/user_schema.py` responsable de validar y sanitizar los datos de entrada.
- **AuthService**: El componente `AuthService` definido en `services/auth_service.py` responsable de la lógica de negocio del registro.
- **UserRepository**: El componente `UserRepository` definido en `repositories/user_repository.py` responsable de persistir y consultar usuarios.
- **User**: El modelo de datos que representa a un usuario en la base de datos con campos `id`, `username`, `email` y `password_hash`.
- **RegisterInput**: El objeto de transferencia de datos validado que contiene `username`, `email` y `password` limpios.
- **password_hash**: La representación segura de la contraseña generada por Werkzeug (`generate_password_hash`).

---

## Requirements

### Requirement 1: Recepción y validación de datos de entrada

**User Story:** Como usuario, quiero registrarme con mi nombre, correo y contraseña, para poder crear una cuenta en la aplicación.

#### Acceptance Criteria

1. WHEN el endpoint `POST /auth/register` recibe una solicitud, THE Validator SHALL extraer los campos `username`, `email` y `password` del cuerpo JSON.
2. WHEN el campo `username` está vacío o ausente, THE Validator SHALL rechazar la solicitud con un mensaje de error que indique que el nombre de usuario es requerido.
3. WHEN el campo `username` tiene menos de 3 caracteres después de eliminar espacios en blanco, THE Validator SHALL rechazar la solicitud con un mensaje de error que indique el mínimo requerido.
4. WHEN el campo `email` está vacío, ausente o no cumple el formato `local@domain.tld`, THE Validator SHALL rechazar la solicitud con un mensaje de error que indique que el correo no es válido.
5. WHEN el campo `password` tiene menos de 6 caracteres o está ausente, THE Validator SHALL rechazar la solicitud con un mensaje de error que indique el mínimo requerido.
6. WHEN todos los campos son válidos, THE Validator SHALL devolver un `RegisterInput` con `username` sin espacios extremos, `email` en minúsculas y `password` sin modificar.

---

### Requirement 2: Unicidad de correo electrónico y nombre de usuario

**User Story:** Como usuario, quiero recibir un mensaje claro si mi correo o nombre de usuario ya están registrados, para poder usar credenciales diferentes.

#### Acceptance Criteria

1. WHEN el `AuthService` recibe un `RegisterInput` cuyo `email` ya existe en la base de datos, THE AuthService SHALL lanzar un `ValueError` con un mensaje que indique que ya existe una cuenta con ese correo.
2. WHEN el `AuthService` recibe un `RegisterInput` cuyo `username` ya existe en la base de datos, THE AuthService SHALL lanzar un `ValueError` con un mensaje que indique que el nombre de usuario ya está en uso.
3. WHILE el `email` del `RegisterInput` no está registrado y el `username` tampoco está registrado, THE AuthService SHALL continuar con la creación del usuario.

---

### Requirement 3: Creación segura del usuario

**User Story:** Como usuario, quiero que mi contraseña se almacene de forma segura, para que mis credenciales estén protegidas aunque la base de datos sea comprometida.

#### Acceptance Criteria

1. WHEN el `AuthService` crea un nuevo usuario, THE AuthService SHALL generar el `password_hash` utilizando `werkzeug.security.generate_password_hash` antes de persistir el objeto `User`.
2. THE UserRepository SHALL persistir el nuevo objeto `User` en la base de datos mediante una sesión SQLAlchemy y confirmar la transacción con `commit`.
3. WHEN la persistencia falla por una excepción de base de datos, THE UserRepository SHALL propagar la excepción al llamador sin ocultar el error.

---

### Requirement 4: Respuesta del endpoint de registro

**User Story:** Como usuario, quiero recibir una confirmación con mi `id` y `username` después de registrarme, para saber que mi cuenta fue creada correctamente.

#### Acceptance Criteria

1. WHEN el registro es exitoso, THE API SHALL devolver una respuesta HTTP 201 con un cuerpo JSON que contenga los campos `message`, `id` y `username`.
2. WHEN el `Validator` rechaza la solicitud por datos inválidos, THE API SHALL devolver una respuesta HTTP 400 con un cuerpo JSON que contenga el campo `error` con el mensaje descriptivo correspondiente.
3. WHEN el `AuthService` rechaza la solicitud por unicidad (`email` o `username` duplicado), THE API SHALL devolver una respuesta HTTP 400 con un cuerpo JSON que contenga el campo `error` con el mensaje descriptivo correspondiente.
4. THE API SHALL aceptar únicamente solicitudes con cuerpo en formato JSON al endpoint `POST /auth/register`.

---

### Requirement 5: Normalización de datos de entrada

**User Story:** Como usuario, quiero que mi correo se almacene de forma uniforme, para que pueda iniciar sesión con cualquier variación de mayúsculas/minúsculas en el correo.

#### Acceptance Criteria

1. WHEN el Validator procesa el campo `email`, THE Validator SHALL convertir el valor a minúsculas antes de incluirlo en el `RegisterInput`.
2. WHEN el Validator procesa el campo `username`, THE Validator SHALL eliminar los espacios en blanco al inicio y al final antes de incluirlo en el `RegisterInput`.
3. THE AuthService SHALL persistir el `email` en minúsculas y el `username` sin espacios extremos tal como los recibe del `RegisterInput`.
