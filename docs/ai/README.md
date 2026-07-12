# AI Prompt Versioning

## Overview

This directory contains versioned AI prompts used throughout the RentSecureBE project.

Every prompt follows the standardized format defined in `docs/ai-governance/AI-UML-Standards.md`.

## Structure

```
docs/ai/
└── prompts/
    └── v1/
        ├── architecture/
        │   ├── adr-generation.prompt.md
        │   ├── diagram-generation.prompt.md
        │   └── code-review.prompt.md
        ├── ci/
        │   ├── pipeline-optimization.prompt.md
        │   └── workflow-generation.prompt.md
        ├── cd/
        │   ├── deployment-planning.prompt.md
        │   └── infrastructure-design.prompt.md
        ├── security/
        │   ├── vulnerability-analysis.prompt.md
        │   └── compliance-check.prompt.md
        ├── uml/
        │   ├── class-diagram.prompt.md
        │   ├── sequence-diagram.prompt.md
        │   └── deployment-diagram.prompt.md
        ├── deployment/
        │   ├── aws-deployment.prompt.md
        │   └── docker-compose.prompt.md
        ├── review/
        │   ├── code-review.prompt.md
        │   └── architecture-review.prompt.md
        └── documentation/
            ├── readme-generation.prompt.md
            └── api-docs.prompt.md
```

## Prompt Format

Every prompt file must contain:

```markdown
# Prompt Title

## Version
v1.0.0

## Author
[Author Name]

## Created Date
YYYY-MM-DD

## Updated Date
YYYY-MM-DD

## Compatible Repository Version
>=2.0.0

## Purpose
[Description of what this prompt does]

## Inputs
- Input 1
- Input 2

## Outputs
- Output 1
- Output 2

## Limitations
- Limitation 1
- Limitation 2

## Usage
\```bash
prompt-engine --prompt v1/architecture/adr-generation.prompt.md --input ...
\```
```

## Versioning Policy

- Prompts are versioned independently
- Major version bumps indicate breaking changes to the prompt format
- Minor version bumps indicate new capabilities
- Patch version bumps indicate clarifications or fixes

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.0.0 | 2026-07-13 | Kilo | Initial prompt templates |
