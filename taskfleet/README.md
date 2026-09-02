# TaskFleet for grant-intelligence

TaskFleet dispatches parallel LLM workers to write tests.

**Config**: `~/taskfleet-configs/grant-intelligence/`

## Quick Start

```bash
./scripts/run-taskfleet.sh --status
./scripts/run-taskfleet.sh --dry-run --task TEST-PY-1
./scripts/run-taskfleet.sh --once
```

## Tasks

- TEST-PY-1: Unit tests for _fits() in Python
- TEST-PY-2: Unit tests for _themeScore() in Python  
- TEST-JS-1: JavaScript _fits() unit tests
- TEST-JS-2: JavaScript matchProfile() parity tests

## Files

- `~/taskfleet-configs/grant-intelligence/config/tasks.json`
- `~/taskfleet-configs/grant-intelligence/config/workers.json`
- `~/taskfleet-configs/grant-intelligence/config/prompts/worker.md`

From [riemann-research/taskfleet](https://github.com/tobias-weiss-ai-xr/riemann-research/tree/main/taskfleet).
