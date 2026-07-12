# AI Contribution Guide

## Overview

This guide explains how to contribute AI-generated content to the RentSecureBE project.

## Workflow

### 1. Preparation
- Understand the existing codebase
- Review relevant documentation
- Check existing prompts in `docs/ai/prompts/`

### 2. Generation
- Use appropriate prompt from `docs/ai/prompts/`
- If no prompt exists, request a new one via ADR
- Generate content using the prompt
- Verify generated content against source code

### 3. Validation
- Run `scripts/diagrams/validate_diagrams.py` for diagrams
- Run tests for code
- Run linting and type checking
- Verify no secrets or credentials are exposed

### 4. Review
- Create PR with AI-generated content
- Include note in PR description:
  - Which prompts were used
  - Which files are AI-generated
  - How the content was validated
- Request review from appropriate team members

### 5. Merge
- All CI checks must pass
- Architecture guard must not flag violations
- At least one human approval required
- Merge and monitor

## Creating New Prompts

1. Identify the need for a new prompt
2. Create prompt file in appropriate category directory
3. Add metadata block
4. Test prompt with sample inputs
5. Submit for review via PR
6. Update this guide if needed

## Troubleshooting

If AI-generated content is not working:
1. Check the prompt version
2. Verify input data
3. Review generated content for errors
4. Escalate to human reviewer if needed
