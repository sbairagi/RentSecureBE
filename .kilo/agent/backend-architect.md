# backend-architect

Django/DRF architecture specialist.

## Configuration

```jsonc
{
  "agent": {
    "backend-architect": {
      "model": "anthropic/claude-opus-4.1",
      "variant": "primary",
      "mode": "subagent",
      "description": "Django/DRF architecture specialist",
      "prompt": ".kilo/prompts/backend-architecture.md",
      "permission": {
        "read": "allow",
        "edit": { "core/": "allow", "tests/": "allow" },
        "bash": { "python manage.py": "allow", "pytest": "allow" }
      }
    }
  }
}
```

## Routing

- CLI: `--agent backend-architect`
- TUI: `Ctrl+O` agent cycle
