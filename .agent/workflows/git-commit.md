---
description: Generate a comprehensive git commit message and commit recent changes
---

1. **Check Status**: Run `git status` to identify unstaged and staged changes.
2. **Review Diff**: Run `git diff` (and `git diff --cached`) to understand the specific code modifications.
3. **Analyze Changes**: Evaluate the purpose of the changes (e.g., bug fix, feature, refactoring, documentation).
4. **Generate Message**: Compose a commit message following the project's specific style:
    - **Format**: `<type>: <summary>` (e.g., `feat: complete Phase 1.2 - ...` or `docs: update documentation`).
    - **Types**: Use standard prefixes: `feat`, `fix`, `docs`, `refactor`, `chore`.
    - **Body**: Use bulleted lists (starting with `- `) to detail specific changes, such as:
        - `- Implemented X feature`
        - `- Fixed Y bug in Z file`
        - `- Updated documentation for A`
5. **Execute Commit**: Execute commit:
    - Stage the files: `git add .` (or specific files if requested).
    - Commit with the message: `git commit -m "<message>"`.
6. **Verify**: Run `git log -n 1` to confirm the commit was successful.