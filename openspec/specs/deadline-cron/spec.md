# Spec: deadline-cron

## Purpose

Requirements derived from initial grant catalog expansion (expand-grant-sources change).

---

## Requirements

### Requirement: Cron wrapper script
The system SHALL provide a shell script `mcp/cron_check_expired.sh` that runs
`python3 update_catalog.py --check-expired` and logs output to a defined log
path (`/var/log/grant-intelligence/expired.log` with directory creation). The
script SHALL exit with code 0 on success, 1 on failure.

#### Scenario: Cron script runs successfully
- **WHEN** `bash cron_check_expired.sh` is executed and no expired deadlines
  exist.
- **THEN** the script SHALL exit with code 0 and the log file SHALL be created
  with a timestamp entry.

#### Scenario: Cron script logs expired deadlines
- **WHEN** `bash cron_check_expired.sh` is executed and expired deadlines
  exist.
- **THEN** the log file SHALL contain the expired programme names and days
  since expiration.

### Requirement: Cron schedule documented
The documentation (README or SPEC-Update-Pipeline) SHALL include a crontab
line and an optional systemd timer unit example for weekly execution of the
deadline check (recommended: Sunday 06:00).

#### Scenario: Crontab example present in docs
- **WHEN** `docs/SPEC-Update-Pipeline.md` is read.
- **THEN** it SHALL contain a crontab line for weekly deadline checking.

### Requirement: Deadline warnings include actionable info
The `check_expired()` output SHALL include the programme ID, name, deadline
date, days since expiration, and source URL so the operator can take immediate
action (check portal, update or remove the entry).

#### Scenario: Warning output is actionable
- **WHEN** a programme is expired.
- **THEN** the warning SHALL include `id`, `name`, `frist`, `tage_abgelaufen`,
  and `quelle`.
