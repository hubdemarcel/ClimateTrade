# Contributing to ClimateTrade

## Guidelines for Maintaining Documentation

To ensure our documentation remains a reliable and useful resource, we treat it with the same care as our code. Outdated documentation can be more harmful than no documentation at all.

### The Golden Rule: Documentation is Part of the "Definition of Done"

Any code change that alters functionality, adds a feature, fixes a bug, or changes a process is not complete until the relevant documentation has been updated.

- **Update docs in the same Pull Request**: All documentation updates should be included in the same pull request as the code changes they relate to. This ensures that code and documentation are reviewed and merged together.
- **Review for Documentation**: During pull request reviews, reviewers are responsible for checking not only the code but also for ensuring that corresponding documentation has been updated accurately.

## Specific Instructions by Document Type

To make this process clearer, here are specific triggers for updating key documents:

### 1. Core Technical & Setup Guides

These documents are critical for developers and new team members.

#### API_DOCUMENTATION.md

- **When to update**: A new endpoint is added, an existing endpoint's request/response format changes, or authentication logic is modified.
- **Instruction**: Use a tool like Postman to test your changes, then export the request/response examples and update the markdown file.
- **Future Goal**: Consider an OpenAPI specification which can be generated from code annotations.

#### DATABASE_DOCUMENTATION.md

- **When to update**: You modify the schema.sql, add a database migration, or change a table/view's purpose.
- **Instruction**: Update the schema diagram or table descriptions to reflect the new structure. Explain the reason for the change.

#### SETUP_GUIDE.md

- **When to update**: A new dependency is added (requirements.txt, package.json), an environment variable is introduced, or the local setup process changes.
- **Instruction**: Before submitting your PR, run through the setup instructions from a clean state to verify they are still correct.

### 2. Operational & Deployment Guides

These are vital for the team responsible for running the system in production.

#### DEPLOYMENT_GUIDE.md

- **When to update**: The deployment process changes, a new step is added to the CI/CD pipeline, or the command to start the application is modified.
- **Instruction**: Clearly list the steps in order. If scripts are used, ensure the commands and their parameters are documented.

### 3. Data & Project Overview

#### PROJECT_OVERVIEW.md

- **When to update**: At the start/end of a major project phase or when the core business goals of the project are adjusted.
- **Instruction**: This should be reviewed periodically (e.g., quarterly) by the project lead to ensure it still aligns with the project's direction.

## General Documentation Best Practices

- **Clarity First**: Write for your audience - assume readers have basic knowledge but not project-specific context
- **Include Examples**: Provide concrete examples wherever possible
- **Version Control**: Keep documentation in the same repository as code for version consistency
- **Regular Reviews**: Schedule periodic documentation reviews to ensure accuracy
- **Link Related Documents**: Use cross-references to connect related documentation
- **Standardize Format**: Use consistent formatting, headings, and terminology across all docs

## Code Contribution Guidelines

### Pull Request Process

1. Ensure all tests pass
2. Update relevant documentation as part of your changes
3. Request review from at least one team member
4. Address review feedback promptly
5. Merge only after all approvals and CI checks pass

### Code Style

- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript/TypeScript
- Maintain consistent naming conventions
- Add docstrings to all public functions and classes

### Testing

- Write tests for new features
- Ensure existing tests still pass
- Aim for good test coverage
- Include integration tests for critical paths

## Project Structure Proposal

### Current Structure Analysis

The current project structure has several organizational issues that impact maintainability and scalability:

#### Key Problems Identified

1. **Scripts Directory Overload**

   - The `scripts/` directory contains 9+ subdirectories that are essentially separate projects or libraries
   - This creates confusion between utility scripts and full-fledged components
   - Examples: `agents/`, `meteostat-python/`, `polymarket-client/`, `real-time-data-client/`

2. **Inconsistent Naming Conventions**

   - Mixed use of hyphens (`met-office-utilities`), underscores (`backtesting_framework`), and camelCase (`Weather2Geo`)
   - No clear standard across the project

3. **Scattered Testing Structure**

   - Tests located in multiple places: `tests/`, `scripts/*/tests/`, `backtesting_framework/*/tests/`
   - No centralized testing strategy

4. **Mixed Concerns at Root Level**
   - Project configuration files mixed with source directories
   - No clear separation between application code, libraries, and tools

### Proposed New Structure

```
climatetrade/
├── .github/                    # GitHub workflows and templates
├── docs/                       # Documentation (current)
├── config/                     # Configuration files
│   ├── pytest.ini
│   └── package-lock.json
├── src/                        # Main application source code
│   ├── weather/               # Weather-related functionality
│   ├── trading/               # Trading and market logic
│   ├── data/                  # Data processing and pipelines
│   └── utils/                 # Shared utilities
├── libs/                       # External libraries and clients
│   ├── weather/
│   │   ├── meteostat/
│   │   ├── met-office/
│   │   ├── weather-gov/
│   │   └── weather-underground/
│   ├── trading/
│   │   ├── polymarket/
│   │   └── resolution-subgraph/
│   └── agents/                 # AI agents system
├── tools/                      # Development and utility scripts
│   ├── scrapers/
│   ├── integrations/
│   └── setup/
├── tests/                      # Centralized test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── web/                        # Web application (current structure maintained)
│   ├── backend/
│   └── frontend/
├── database/                   # Database schemas and migrations (current)
├── analysis/                   # Analysis tools (current)
└── backtesting_framework/      # Backtesting system (current)
```

### Migration Plan

#### Phase 1: Library Extraction

- Move `scripts/agents/` → `libs/agents/`
- Move `scripts/meteostat-python/` → `libs/weather/meteostat/`
- Move `scripts/met-office-utilities/` → `libs/weather/met-office/`
- Move `scripts/weather-gov-api/` → `libs/weather/weather-gov/`
- Move `scripts/Weather2Geo/` → `libs/weather/weather2geo/`

#### Phase 2: Tool Organization

- Move `scripts/polymarket-scraper/` → `tools/scrapers/polymarket/`
- Move `scripts/polymarket-client/` → `libs/trading/polymarket/`
- Move `scripts/real-time-data-client/` → `libs/trading/real-time-data/`
- Move `scripts/resolution-subgraph/` → `libs/trading/resolution-subgraph/`

#### Phase 3: Test Consolidation

- Move all `*/tests/` directories to centralized `tests/` structure
- Update import paths in test files
- Standardize test naming conventions

#### Phase 4: Configuration Cleanup

- Move `pytest.ini` → `config/pytest.ini`
- Move `package-lock.json` → `config/package-lock.json` (if applicable)
- Create `.gitignore` patterns for new structure

#### Phase 5: Naming Standardization

- Convert all directory names to use underscores: `met_office_utilities` → `met_office_utilities`
- Update all import statements and references
- Update documentation and scripts

### Benefits of Proposed Structure

1. **Clear Separation of Concerns**

   - Libraries vs. application code vs. tools
   - Domain-based organization (weather, trading, data)

2. **Improved Maintainability**

   - Centralized testing
   - Consistent naming conventions
   - Logical grouping of related functionality

3. **Better Scalability**

   - Easy to add new domains or libraries
   - Clear paths for new team members
   - Reduced cognitive load when navigating the codebase

4. **Enhanced Developer Experience**
   - Predictable file locations
   - Reduced time spent searching for code
   - Cleaner dependency management

## Getting Help

If you're unsure about any contribution guidelines or documentation requirements:

- Check existing documentation for similar changes
- Ask in team chat or during standups
- Review recent pull requests for examples
- Contact the project maintainers

Thank you for helping maintain high-quality code and documentation!