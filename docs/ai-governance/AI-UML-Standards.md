# AI UML Standards

## Overview

All AI-generated UML diagrams must follow these standards to ensure consistency and usefulness.

## Diagram Types

### Class Diagrams
- Show all models with fields and types
- Show relationships (ForeignKey, OneToOne, ManyToMany)
- Show inheritance
- Include multiplicities
- Use standard UML notation

### Sequence Diagrams
- Show all participants
- Show message flow with arrows
- Show activation bars
- Show alternative paths (alt, opt, par)
- Include notes for clarity

### Component Diagrams
- Show high-level components
- Show dependencies between components
- Show interfaces
- Use component notation

### Deployment Diagrams
- Show infrastructure components
- Show network connections
- Show cloud services
- Use deployment notation

### C4 Diagrams
- Follow C4 model hierarchy (Context, Container, Component, Code)
- Use standard C4 notation
- Include legends
- Keep diagrams focused on one level

### Activity Diagrams
- Show workflow steps
- Show decision points
- Show parallel flows
- Show start and end nodes

### State Diagrams
- Show states
- Show transitions
- Show events that trigger transitions
- Show initial and final states

### ER Diagrams
- Show all models as entities
- Show relationships with cardinality
- Show primary keys
- Show foreign keys

## Standards

### PlantUML
- Use `@startuml` / `@enduml` tags
- Use skinparams for styling
- Keep diagrams readable at 100% zoom
- Use meaningful names for elements

### Mermaid
- Use appropriate diagram type declaration
- Use standard Mermaid syntax
- Keep diagrams simple and focused
- Use subgraphs for grouping

### C4
- Use C4-PlantUML or C4-Mermaid syntax
- Follow C4 model hierarchy
- Include person and system boundaries
- Use standard colors for element types

## Validation

All generated diagrams must:
- Pass syntax validation
- Render without errors
- Be committed to version control
- Be referenced in documentation

## Automation

Diagrams must be generated automatically via:
- `scripts/diagrams/generate_plantuml.py`
- `scripts/diagrams/generate_mermaid.py`
- `scripts/diagrams/generate_c4.py`
- `scripts/diagrams/generate_domain_diagrams.py`
- `scripts/diagrams/generate_flow_diagrams.py`
- `scripts/diagrams/generate_infrastructure_diagrams.py`
- `scripts/diagrams/generate_ddd_diagrams.py`

Manual edits to generated diagrams are not allowed.
