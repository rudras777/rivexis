#!/usr/bin/env python3
from __future__ import annotations
import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'apps'/'api'))
from rivexis_api.services.retention import policy
p=policy();assert p['provider_requests_days']>0;assert p['audit_logs_days']>0;assert p['reports_days']==0;assert not p['delete_enabled'];assert not p['report_delete_enabled']
print('Retention policy gate: PASS (telemetry/audit bounded; reports indefinite by default; deletion opt-in)')
