# Requisitos — Login de usuario

## Introducción

Este feature extiende el endpoint `/auth/login` (POST) de la API REST en Flask para que acepte tanto el **correo electrónico** como el **nombre de usuario** como identificador al momento de autenticarse. Actualmente el login solo admite email + contraseña; el objetivo es permitir que los usuarios que se registraron con `username`, `email` y `password` (vía `/auth/register`) puedan iniciar sesión usando cualquiera de los dos identificadores junto con su contraseña.

La implementación sigue la arquitectura en capas del proyecto: `controllers → services → repositories → models`.

---

## Requisitos

### 1. Login con correo electrónico y contraseña

**Historia de usuario:** Como usuario registrado, quiero iniciar sesión con mi correo electrónico y contraseña, para acceder a mi cuenta de forma segura.

#### Criterios de aceptación

1. CUANDO el usuario envía una petición POST a `/auth/login` con un `email` válido y la `password` correcta ENTONCES el sistema autentica al usuario Y devuelve una respuesta exitosa con los datos del usuario y un token de acceso.
2. CUANDO el usuario envía una petición POST a `/auth/login` con un `email` con formato inválido ENTONCES el sistema rechaza la petición Y devuelve un error de validación con código HTTP 400.

---

### 2. Login con nombre de usuario y contraseña

**Historia de usuario:** Como usuario registrado, quiero iniciar sesión con mi nombre de usuario y contraseña, para tener una alternativa al correo electrónico como identificador.

#### Criterios de aceptación

1. CUANDO el usuario envía una petición POST a `/auth/login` con un `username` válido y la `password` correcta ENTONCES el sistema autentica al usuario Y devuelve una respuesta exitosa con los datos del usuario y un token de acceso.
2. CUANDO el usuario envía una petición POST a `/auth/login` con un `username` que no existe en el sistema ENTONCES el sistema rechaza la petición Y devuelve un error de credenciales inválidas con código HTTP 401.

---

### 3. Validación de campos obligatorios

**Historia de usuario:** Como sistema, quiero validar que la petición de login contenga los campos mínimos requeridos, para evitar procesar solicitudes incompletas.

#### Criterios de aceptación

1. CUANDO el usuario envía una petición POST a `/auth/login` sin incluir ni `email` ni `username` ENTONCES el sistema rechaza la petición Y devuelve un error de validación indicando que al menos un identificador es obligatorio, con código HTTP 400.
2. CUANDO el usuario envía una petición POST a `/auth/login` sin incluir el campo `password` ENTONCES el sistema rechaza la petición Y devuelve un error de validación indicando que la contraseña es obligatoria, con código HTTP 400.
3. CUANDO el usuario envía una petición POST a `/auth/login` con el cuerpo vacío o sin formato JSON válido ENTONCES el sistema rechaza la petición Y devuelve un error de validación con código HTTP 400.

---

### 4. Respuesta de error por credenciales incorrectas

**Historia de usuario:** Como sistema, quiero retornar un error claro cuando las credenciales no son válidas, para proteger la cuenta del usuario sin revelar información sensible.

#### Criterios de aceptación

1. CUANDO el usuario envía una petición POST a `/auth/login` con un `email` existente pero con una `password` incorrecta ENTONCES el sistema rechaza la autenticación Y devuelve un mensaje de error genérico de credenciales inválidas con código HTTP 401.
2. CUANDO el usuario envía una petición POST a `/auth/login` con un `username` existente pero con una `password` incorrecta ENTONCES el sistema rechaza la autenticación Y devuelve un mensaje de error genérico de credenciales inválidas con código HTTP 401.
3. CUANDO el sistema devuelve un error de credenciales inválidas ENTONCES el mensaje de error no debe revelar si el identificador existe o no en la base de datos Y debe ser el mismo mensaje independientemente del campo incorrecto.

---

### 5. Respuesta exitosa con datos del usuario

**Historia de usuario:** Como usuario autenticado, quiero recibir mis datos y un token de acceso al iniciar sesión correctamente, para poder realizar peticiones autenticadas a la API.

#### Criterios de aceptación

1. CUANDO el login es exitoso ENTONCES el sistema devuelve una respuesta con código HTTP 200 Y el cuerpo incluye el `id`, `username` y `email` del usuario autenticado.
2. CUANDO el login es exitoso ENTONCES el sistema incluye en la respuesta un token de acceso válido Y el token puede ser usado para autenticar peticiones subsiguientes a endpoints protegidos.
3. CUANDO el login es exitoso ENTONCES la respuesta no debe incluir la `password` ni ningún hash de contraseña del usuario.
