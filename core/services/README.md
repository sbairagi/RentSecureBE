# Core Service Layer

This package contains the service layer structure for the `core` app.

## Purpose

Services contain business logic. Views orchestrate HTTP requests and delegate
to services. Services must not contain HTTP-specific logic.

## Rules

- Views orchestrate requests.
- Services contain business logic.
- Models contain persistence concerns only.
- No HTTP logic inside services.
