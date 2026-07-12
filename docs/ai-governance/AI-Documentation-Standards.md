# AI Documentation Standards

## Overview

All AI-generated documentation must follow these standards to ensure consistency and quality.

## Standards

### Markdown Formatting
- Use GitHub-flavored Markdown
- Maximum line length: 120 characters
- Use proper heading hierarchy (H1 → H2 → H3)
- Use code blocks with language identifiers
- Use tables for structured data

### Documentation Types

#### README Files
- Must include project description
- Must include setup instructions
- Must include usage examples
- Must include contribution guidelines

#### Architecture Documentation
- Must include diagrams
- Must include decision rationale
- Must include trade-offs
- Must include alternatives considered

#### API Documentation
- Must include endpoint descriptions
- Must include request/response examples
- Must include error codes
- Must include authentication requirements

#### Code Documentation
- All public functions must have docstrings
- Docstrings must follow Google style
- Docstrings must include parameters, return values, and exceptions
- Complex algorithms must have inline comments

### Diagram Standards
- Diagrams must use standard notation (PlantUML, Mermaid, C4)
- Diagrams must be stored in version control
- Diagrams must be generated from source, not manually edited
- Diagrams must include legend/keys when necessary

### Versioning
- All docs must include version number
- All docs must include last updated date
- All AI-generated docs must indicate the prompt version used

## Review Process

1. AI generates documentation
2. Human reviews for accuracy
3. Human checks formatting and standards compliance
4. Approved docs are committed
