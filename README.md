# MnemonicTrace — Architecture Scaffold

This repository contains a structure-only scaffold for a modular Python service. The application logic is intentionally unimplemented.

## Architecture

- `domain/`: pure domain types and rules; no I/O or infrastructure imports
- `ports/`: abstract contracts for data sources, storage, and optional acceleration
- `adapters/`: replaceable infrastructure integrations
- `workers/`: worker orchestration placeholders
- `pipeline/`: shard manifest and scheduler placeholders
- `api/`: FastAPI entry point and dependency wiring placeholder
- `web/`: static frontend placeholder intended for separate hosting
- `miniapp/`: Telegram Mini App placeholder
- `infra/`: container and local orchestration placeholders
- `tests/`: test-first placeholders

No domain algorithms, scanning logic, derivation code, network clients, or worker behavior is implemented. Add reviewed tests before implementation.

## Local configuration

Copy `.env.example` to `.env` and use development-only values. Do not commit secrets, wallet recovery phrases, private keys, access tokens, or sensitive datasets.
