# AIPPT

AIPPT is a multi-user AI PPT generation platform for SJTU-style presentations.

The product flow is intentionally conservative:

1. A user logs in and creates a private deck session.
2. The planner turns the user's request into an editable Markdown outline.
3. The outline is converted into a constrained Deck IR.
4. A deterministic builder generates an SJTU-style PPTX.
5. A worker runs QA and writes job logs and artifacts.

Hermes Agent is used as a constrained worker inside each job workspace. It should
not be the component that owns user identity, authorization, storage, or final
layout decisions.

## Repository Layout

```text
apps/api/          Multi-user API, auth, deck sessions, jobs
packages/builder/  Deterministic Markdown/Deck IR to PPTX builder
docs/              Product, architecture, deployment, and skill docs
ops/               Server bootstrap and operational scripts
```

Useful starting docs:

- [Architecture](docs/aippt_architecture.md)
- [Authentication](docs/aippt_auth.md)
- [Implementation plan](docs/aippt_implementation_plan.md)
- [Frontend plan](docs/aippt_frontend_plan.md)
- [Operations playbook](docs/aippt_ops_playbook.md)
- [Hermes deployment notes](docs/aippt_hermes_deployment.md)

## Development Priorities

1. Lock down multi-user data ownership in the API.
2. Build a minimal deterministic PPTX builder.
3. Add job workspace creation and QA scripts.
4. Add a web UI for Markdown outline editing and downloads.
5. Wire Hermes into the job worker loop for IR repair and failure recovery.

## Server

Public campus route:

```text
https://ai4edu.sjtu.edu.cn/ppt/
```

The current development server is available through:

```bash
ssh aippt
```

Server layout:

```text
/srv/aippt/
  app/
  builder/
  env/
  jobs/
  logs/
  shared/
  vendor/hermes-agent/
  venvs/ppt-builder/
```
