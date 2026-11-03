# Repository instructions

Read [engineering standards](docs/architecture/ENGINEERING_STANDARDS.md) and the relevant architecture/runbook before editing. Follow nested instructions, including `apps/web/AGENTS.md`.

Preserve the existing product, financial precision, authentication, users and infrastructure. Use the current checkpoint and evidence dates; never turn a historical result into a fresh verification claim. Keep credentials, browser sessions and protected recovery material out of source and logs. Make narrow changes, run relevant checks, update the checkpoint and use protected pull requests. Do not rename or remove deployed resources, rewrite history, reset data, change DNS, rotate credentials or add spending without the required specific authorization.

Development preview and fixture tests must not use production customer data. Ordinary tools and documented commands must remain sufficient to maintain the project.
