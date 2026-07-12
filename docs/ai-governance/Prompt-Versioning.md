# Prompt Versioning

## Overview

All AI prompts in this project follow a strict versioning scheme to ensure reproducibility and traceability.

## Directory Structure

```
docs/ai/prompts/
└── v1/
    ├── architecture/
    ├── ci/
    ├── cd/
    ├── security/
    ├── uml/
    ├── deployment/
    ├── review/
    └── documentation/
```

## Prompt Metadata Format

Every prompt file must include this metadata block:

```markdown
---
version: 1.0.0
author: Name <email>
created: YYYY-MM-DD
updated: YYYY-MM-DD
compatible: ">=2.0.0"
purpose: Brief description
inputs:
  - input1
  - input2
outputs:
  - output1
  - output2
limitations:
  - limitation1
  - limitation2
usage: |
  prompt-engine --prompt v1/category/name.prompt.md --input ...
tags:
  - architecture
  - uml
---
```

## Version Bumping

- **Major (X.0.0)**: Breaking changes to prompt format or required inputs
- **Minor (X.Y.0)**: New capabilities, additional inputs/outputs
- **Patch (X.Y.Z)**: Clarifications, typos, minor improvements

## Review Process

1. Create prompt in appropriate category directory
2. Add metadata block
3. Test prompt with sample inputs
4. Submit for review
5. Once approved, bump version if needed

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-13 | Kilo | Initial prompt templates |
