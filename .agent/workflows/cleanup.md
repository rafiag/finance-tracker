---
description: Stop all development processes (Docker, Python, Dev Servers) and perform workspace cleanup
---

1. **Stop Docker Containers**: Run `docker compose down` to stop and remove all project containers.
// turbo
2. **Kill Lingering Python Processes**: Stop any active Python instances to free up resources.
   - Command: `Get-Process | Where-Object { $_.Name -like "python*" } | Stop-Process -Force -ErrorAction SilentlyContinue`
// turbo
3. **Kill Dev Servers/Node Processes**: Terminate any Node.js, NPM, or Vite processes running on the host.
   - Command: `Get-Process | Where-Object { $_.Name -match "node|npm|vite" } | Stop-Process -Force -ErrorAction SilentlyContinue`
4. **Prune Docker (Optional)**: If requested, run `docker system prune -f` to remove unused data.
5. **Clean Workspace Caches**: Remove temporary folders and cache files to keep the directory clean.
   - Target folders: `**/__pycache__`, `**/.pytest_cache`, `**/dist`, `**/build`, `**/.doc_cache`.
   - Command: `Get-ChildItem -Path . -Include __pycache__,.pytest_cache,dist,build,.doc_cache -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue`
6. **Verify**: Run `docker ps` and `Get-Process python*` to ensure everything is stopped.
