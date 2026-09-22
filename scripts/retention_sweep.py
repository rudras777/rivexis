#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps'/'api'))
from rivexis_api.services.retention import apply_retention, retention_plan

p=argparse.ArgumentParser(description='Preview or apply Rivexis retention policy.')
p.add_argument('--workspace-id');p.add_argument('--apply',action='store_true')
a=p.parse_args()
try: result=apply_retention(workspace_id=a.workspace_id) if a.apply else retention_plan(workspace_id=a.workspace_id)
except PermissionError as exc:
    print(json.dumps({'status':'REFUSED','reason':str(exc)},indent=2));raise SystemExit(2)
print(json.dumps(result,indent=2,sort_keys=True))
