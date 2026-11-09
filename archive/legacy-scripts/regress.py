# LEGACY (requirement 1.1 workflow). Kept for traceability only; not used by the 1.3 pipeline.
# finalize.py contained templated "author" scores that were withdrawn in 1.3 (see archive/superseded/).
"""Rerun specific defect cases with unchanged request inputs; preserve original runs."""
import json
from xulan.service import ROOT,ConversationService
from xulan.client import OpenAIClient
from xulan.settings import load_credentials
from xulan.budget import BudgetGuard
from xulan.models import GenerationRequest
load_credentials()
folder=ROOT/'runs/v4.1-regression';folder.mkdir(exist_ok=True)
assert not (folder/'manifest.json').exists(),'Preserve previous runs; choose another label.'
service=ConversationService(OpenAIClient(BudgetGuard(ROOT/'runs/budget.sqlite')),folder)
manifest=[]
for e in json.loads((ROOT/'runs/v2.2-final/manifest.json').read_text()):
 if e['case_id'] not in ['T029','T048']:continue
 result=service.generate(GenerationRequest.model_validate(e['request']))
 manifest.append({'case_id':e['case_id'],'version_label':'v4.1-regression','request':e['request'],'result':result.model_dump(mode='json')})
 (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print(e['case_id'],result.status.value,flush=True)
