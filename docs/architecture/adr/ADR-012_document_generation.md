# ADR-012: Document Generation Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs document generation for:
- Rent receipts (PDF)
- Rental agreements (PDF)
- Tax documents (PDF)
- Financial reports (PDF)

Documents must be:
- Generated from templates
- Stored securely
- Accessible to authorized users
- Versioned

---

## Decision

RentSecure uses a **document generation abstraction** with template-based PDF generation.

**Key components:**
- `DocumentService`: Orchestrates document generation
- `TemplateService`: Manages document templates
- `PDFGeneratorAdapter`: Generates PDFs (WeasyPrint)
- `StorageAdapter`: Stores documents (S3)

**Rules:**
- Templates are context-specific (provided by domain contexts)
- Document generation is async for heavy documents
- Documents are stored with access control
- Document metadata is tracked in database

---

## Alternatives Considered

### 1. Direct PDF Generation

**Description:** Generate PDFs directly in services using WeasyPrint.

**Pros:**
- Simple, no abstraction

**Cons:**
- Tight coupling to WeasyPrint
- Hard to switch PDF generators
- Template management scattered
- Hard to test

**Decision:** Rejected. Locks into one PDF library.

### 2. Third-Party Document Service

**Description:** Use a third-party service for document generation.

**Pros:**
- No PDF library maintenance
- Professional templates

**Cons:**
- Additional cost
- External dependency
- Data leaves the platform
- Not viable for Year 1 budget

**Decision:** Rejected. Cost and dependency concerns.

### 3. Document Abstraction (Selected)

**Description:** Abstract document generation behind interfaces.

**Pros:**
- Easy to switch PDF generators
- Template management is centralized
- Testable with mocks
- Supports async generation

**Cons:**
- More code (interface + adapters)
- Template management overhead

**Decision:** Accepted. Best for long-term flexibility.

---

## Document Generation Flow

```
Domain context requests document
    │
    ▼
DocumentService.generate(template_id, context)
    │
    ├──▶ Get template from TemplateService
    ├──▶ Render template with context
    ├──▶ PDFGeneratorAdapter.generate_pdf(rendered_template)
    ├──▶ StorageAdapter.store(pdf, owner_id)
    ├──▶ Create Document record
    └──▶ Return Document
```

---

## Consequences

### Positive
- Easy to switch PDF generators
- Template management is centralized
- Documents are stored with access control
- Async generation for heavy documents
- Easy to test

### Negative
- More code (interface + adapters)
- Template management overhead

### Neutral
- WeasyPrint is the Year 1 implementation
- S3 is the Year 1 storage backend

---

## References

- [Bounded Contexts](../future/02_bounded_contexts.md)
- [Production Architecture](../production-architecture.md)
