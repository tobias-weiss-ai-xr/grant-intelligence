#!/usr/bin/env bash
# Förder-Radar – Deadline-Check (Cron-Wrapper)
# Laeuft wöchentlich, meldet abgelaufene/dringende Fristen.
#
# Crontab-Eintrag (Empfehlung: Sonntag 06:00):
#   0 6 * * 0 /opt/git/grant-intelligence/mcp/cron_check_expired.sh >> /var/log/grant-intelligence/deadline.log 2>&1
#
# Alternativ systemd-Timer (siehe cron_deadline_timer.{service,timer})

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="/var/log/grant-intelligence"
LOG_FILE="${LOG_DIR}/expired.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR" 2>/dev/null || LOG_DIR="$SCRIPT_DIR"
LOG_FILE="${LOG_DIR}/expired.log"

echo "--- Förder-Radar Deadline-Check: $(date -Iseconds) ---" >> "$LOG_FILE"

cd "$SCRIPT_DIR"
python3 update_catalog.py --check-expired >> "$LOG_FILE" 2>&1
# Strukturierter Frist-Digest (dringend/anstehend/abgelaufen, dedupliziert)
python3 deadline_digest.py >> "$LOG_FILE" 2>&1
# Katalog-Qualitätsgate (Datenintegrität; Exit 1 bei strukturellen Fehlern)
python3 catalog_lint.py --fail >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "[ERROR] Deadline-Check fehlgeschlagen (exit $EXIT_CODE)" >> "$LOG_FILE"
fi

echo "--- Ende ---" >> "$LOG_FILE"

exit $EXIT_CODE
