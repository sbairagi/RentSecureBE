# Class Diagram Generation from Django Models

## Version
1.0.0

## Author
RentSecureBE Team

## Created Date
2026-07-13

## Updated Date
2026-07-13

## Compatible Repository Version
>=2.4.0

## Purpose
Generate PlantUML and Mermaid class diagrams by analyzing Django model files using AST parsing.

## Inputs
- Django app directories
- Model files (models.py or models/*.py)
- Output format (plantuml, mermaid)

## Outputs
- PlantUML class diagram
- Mermaid class diagram
- Entity relationship diagram

## Limitations
- Requires valid Python syntax
- Cannot infer runtime relationships
- Abstract base classes may need manual review

## Usage
```bash
python scripts/diagrams/generate_domain_diagrams.py --all
```
