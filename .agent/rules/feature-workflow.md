# Feature Development Rules

These rules govern the implementation of new features within the project to ensure high quality, maintainability, and alignment with project standards.

## 1. Requirement Analysis & Planning
* **Requirement Review**: Before starting any implementation, always review `docs/FEATURE-PLAN.md`, `docs/TECHINICAL-SPEC.md`, and the existing codebase to fully understand the context.
* **Formal Planning**: Always present a detailed implementation plan to the user BEFORE starting work. The plan must include:
    - Technical approach and key components.
    - Step-by-step implementation order.
    - Testing strategy (unit, integration, and E2E).
    - Plain-language explanation of any tradeoffs.
* **Explicit Approval**: Implementation must NOT begin until the user has explicitly approved the plan (e.g., "ok", "approved").

## 2. Environment & Execution
* **Docker Management**: 
    - Ensure Docker services are running (`docker compose up -d`) before starting execution.
    - **Leverage Hot Reloading**: Do NOT rebuild images for standard code changes. Rely on volume syncing for Backend and Frontend code.
    - **Conditional Rebuild**: Only use `docker compose up --build` if modifying dependencies (`requirements.txt`, `package.json`), environment variables, or Dockerfiles.
* **Production Quality**: 
    - All code must be production-ready.
    - **No Placeholders**: Do NOT use "TODO" comments or placeholder code/assets. If images or data are needed, generate real examples using available tools.
* **Python Standards**: Strictly follow PEP 8 for all Python code.
* **Error Handling**: Implement robust error handling with user-friendly messages for all new logic.
* **Complexity Alert**: If an implementation detail becomes significantly more complex than planned, pause and ask for user confirmation before proceeding further.

## 3. Testing & Verification
* **Automated Testing**: Every feature must be verified with automated tests (unit, integration, etc.) before being presented as complete.

## 4. Documentation Standards
* **Feature Documentation**: Every feature must have its own documentation directory: `docs/<feature-name>/`.
* **Required Files**:
    - `docs/<feature-name>/README.md`: High-level overview and setup instructions.
    - `docs/<feature-name>/<FEATURE_NAME>.md`: Technical specifications, architecture details, and API definitions.
* **Cross-Reference Updates**: Update all relevant root documents:
    - `FEATURE-PLAN.md`
    - `TECHINICAL-SPEC.md`
    - `README.md`
    - `CLAUDE.md`
    - Ensure references to the design system documentation `docs/04-design/design-system.md` are maintained for consistency.

## 5. Delivery
* **Demonstration**: Always demonstrate the working feature to the user, providing both technical and user-facing explanations of the results.
