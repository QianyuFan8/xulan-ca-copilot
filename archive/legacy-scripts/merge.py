# LEGACY (requirement 1.1 workflow). Kept for traceability only; not used by the 1.3 pipeline.
# finalize.py contained templated "author" scores that were withdrawn in 1.3 (see archive/superseded/).
"""Select final successful case runs without modifying original attempts."""
import json,csv
from xulan.service import ROOT

folder=ROOT/'runs/v2.2-final'
folder.mkdir(exist_ok=True)
selected={}
for label in ['v2.2-formal','v2.2-tail']:
    for entry in json.loads((ROOT/'runs'/label/'manifest.json').read_text()):
        if entry['result']['status']=='success':selected[entry['case_id']]=entry
manifest=[selected[k] for k in sorted(selected)]
assert len(manifest)==50, f'Only {len(manifest)} successful cases; do not claim completion.'
(folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
with (folder/'test_cases.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['Case ID','Scenario','Client information','Conversation history','Product information','Output 1','Output 2','Output 3'])
    for e in manifest:
        r=e['request'];w.writerow([e['case_id'],r['scenario'],json.dumps(r['client_information'],ensure_ascii=False),json.dumps(r['conversation_history'],ensure_ascii=False),json.dumps(r['product_information'],ensure_ascii=False),*e['result']['candidates']])
print('Selected',len(manifest),'successful cases; original failures retained.')

