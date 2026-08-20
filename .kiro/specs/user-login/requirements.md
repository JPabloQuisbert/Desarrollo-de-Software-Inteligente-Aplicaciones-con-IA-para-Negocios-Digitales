# Requirements Document

## Introduction

This document defines the formal requirements for the **user login** feature of the Flask REST API. The feature allows a registered user to authenticate using an email address or username together with a password. Upon successful authentication, the system returns a signed JWT access token that the client includes in subsequent requests to access protected resources.

The implementation already exists in the codebase (POST /auth/login). These requirements capture the intended behavior formally so that the implementation can be verified, tested, and extended with confidence.

---

## Glossary

- **API**: The Flask REST API application defined in `app.py`.
- **AuthController**: The Flask blueprint in `controllers/auth_controller.py` that handles HTTP routing for authentication endpoints.
- **AuthService**: The business-logic layer in `services/auth_service.py` responsible for verifying credentials.
- **UserRepository**: The data-access layer in `repositories/user_repository.py` responsible for querying the `users` table.
- **UserValidator**: The input-validation component in `schemas/user_schema.py` responsible for sanitizing and validating request payloads.
- **LoginInput**: The validated data-transfer object produced by `UserValidator.validate_login`, containing `email` (optional), `username` (optional), and `password`.
- **User**: A record in the `users` table with fields `id`, `username`, `email`, and `password_hash`.
- **JWT**: A JSON Web Token signed with the application's `JWT_SECRET_KEY` and issued by `flask-jwt-extended`.
- **Access Token**: A JWT that expires 1 hour after issuance and is used by clients to authenticate subsequent API calls.
- **Password Hash**: A Werkzeug-generated bcrypt-based hash stored in `users.password_hash`; the plaintext password is never stored.
- **Identifier**: Either a valid email address or a valid username supplied by the client to identify the account at login.

---

## Requirements

### Requirement 1: Accept Login Request via HTTP

**User Story:** As a registered user, I want to submit my credentials via an HTTP endpoint so that the API can authenticate me.

#### Acceptance Criteria

1. THE AuthController SHALL expose a `POST /auth/login` endpoint that accepts `application/json` request bodies.
2. WHEN the request body is missing or cannot be parsed as JSON, THE AuthController SHALL return HTTP 400 with an `error` field describing the problem.
3. THE AuthController SHALL accept a request body containing at least one of `email` or `username`, and a `password` field.

---

### Requirement 2: Validate Login Input

**User Story:** As a registered user, I want the API to reject malformed credentials early so that I receive a clear error message rather than an ambiguous failure.

#### Acceptance Criteria

1. WHEN the request body contains neither an `email` field nor a `username` field, THE UserValidator SHALL raise a `ValueError` with the message `"Debes proporcionar un correo electrónico o nombre de usuario."`.
2. WHEN the request body contains an `email` field whose value does not match the pattern `^[^@\s]+@[^@\s]+\.[^@\s]+$`, THE UserValidator SHALL raise a `ValueError` with the message `"El correo electrónico no es válido."`.
3. WHEN the request body contains a `username` field whose value has fewer than 3 characters after stripping whitespace, THE UserValidator SHALL raise a `ValueError` with the message `"El nombre de usuario debe tener al menos 3 caracteres."`.
4. WHEN the request body does not contain a non-empty `password` field, THE UserValidator SHALL raise a `ValueError` with the message `"La contraseña es requerida."`.
5. WHEN `UserValidator.validate_login` raises a `ValueError`, THE AuthController SHALL return HTTP 400 with a JSON body containing an `error` field set to the exception message.
6. WHEN input validation passes, THE UserValidator SHALL return a `LoginInput` dataclass with `email` set to the lower-cased, stripped value if an email was provided, `username` set to the stripped value if a username was provided (and no email was provided), and `password` set to the raw password value.

---

### Requirement 3: Look Up the User Account

**User Story:** As a registered user, I want the API to locate my account using either my email or username so that I can log in with the identifier I prefer.

#### Acceptance Criteria

1. WHEN the `LoginInput` contains an `email` value, THE UserRepository SHALL query the `users` table for a record whose `email` column matches that value.
2. WHEN the `LoginInput` does not contain an `email` value and contains a `username` value, THE UserRepository SHALL query the `users` table for a record whose `username` column matches that value.
3. WHEN no matching `User` record is found, THE AuthService SHALL raise a `ValueError` with the message `"Credenciales incorrectas."`.

---

### Requirement 4: Verify Password

**User Story:** As a registered user, I want the API to verify my password securely so that unauthorized parties cannot access my account.

#### Acceptance Criteria

1. WHEN a matching `User` record is found, THE AuthService SHALL verify the provided plaintext password against `User.password_hash` using `werkzeug.security.check_password_hash`.
2. WHEN `check_password_hash` returns `False`, THE AuthService SHALL raise a `ValueError` with the message `"Credenciales incorrectas."`.
3. THE AuthService SHALL return the same error message for an unrecognized identifier and for a wrong password, so that the response does not reveal whether the account exists.

---

### Requirement 5: Issue a JWT Access Token

**User Story:** As a registered user, I want to receive a JWT access token upon successful login so that I can authenticate subsequent requests to protected resources.

#### Acceptance Criteria

1. WHEN `AuthService.login` returns a `User` record, THE AuthController SHALL call `flask_jwt_extended.create_access_token` with `identity` set to the string representation of `User.id`.
2. THE API SHALL issue access tokens that expire 1 hour after the moment of issuance, as configured via `JWT_ACCESS_TOKEN_EXPIRES` in `config.py`.
3. WHEN authentication succeeds, THE AuthController SHALL return HTTP 200 with a JSON body containing the fields `message`, `id`, `username`, `email`, and `access_token`.
4. THE AuthController SHALL NOT include the `password_hash` field in any login response body.

---

### Requirement 6: Return Structured Error Responses

**User Story:** As an API client developer, I want all error responses to follow a consistent JSON structure so that my application can handle failures uniformly.

#### Acceptance Criteria

1. WHEN authentication fails due to incorrect credentials, THE AuthController SHALL return HTTP 401 with a JSON body containing an `error` field set to `"Credenciales incorrectas."`.
2. WHEN the request fails input validation, THE AuthController SHALL return HTTP 400 with a JSON body containing an `error` field set to the validation error message.
3. THE AuthController SHALL NOT return HTTP 500 for foreseeable error conditions such as invalid credentials or malformed input.

---

### Requirement 7: Protect Sensitive Data in Transit

**User Story:** As a registered user, I want the API to handle my credentials carefully so that my password is never exposed in logs or responses.

#### Acceptance Criteria

1. THE AuthService SHALL NOT store or return the plaintext password at any point during the login flow.
2. THE AuthController SHALL NOT include `password` or `password_hash` fields in any response body.
3. WHERE the application is deployed in a production environment, THE API SHALL be served over HTTPS so that credentials are encrypted in transit.
