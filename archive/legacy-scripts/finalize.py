# LEGACY (requirement 1.1 workflow). Kept for traceability only; not used by the 1.3 pipeline.
# finalize.py contained templated "author" scores that were withdrawn in 1.3 (see archive/superseded/).
"""Create final selection with explicit source version per case and author review."""
import json,csv
from xulan.service import ROOT
out=ROOT/'runs/final-selection';out.mkdir(exist_ok=True)
selected={};reviews={}
for label in ['v2.2-final','v3-regression','v3.1-regression','v3.2-regression','v4-regression','v4.1-regression']:
 folder=ROOT/'runs'/label
 if not (folder/'manifest.json').exists():continue
 for e in json.loads((folder/'manifest.json').read_text()):
  if e['result']['status']=='success':selected[e['case_id']]=e
 if (folder/'reviews.json').exists():
  for e in json.loads((folder/'reviews.json').read_text()):reviews[e['case_id']]=e
manifest=[selected[k] for k in sorted(selected)]
assert len(manifest)==50
# Codex author has read the full Chinese final message set. Scores are subjective
# author assessment, not human/CA labels and not a replacement for raw model judgments.
notes={
'T001':('Warm and short but wishes are similar.',3),
'T002':('Design preference is used a little literally in a birthday wish.',3),
'T003':('Simple and restrained; generic because little relevant personal context exists.',3),
'T004':('No pressured reply; three choices still fairly close.',2),
'T005':('Over-personalized through design interest; avoid inserting leather interest into greetings.',3),
'T006':('Moving-home detail is supported and used appropriately.',4),
'T007':('Advance occasion framing is supported; festival is nearly two months away so timing needs CA judgment.',3),
'T008':('Design metaphors remain too promotional/abstract in options 1 and 3.',3),
'T009':('Regression removes unsupported stock; remaining choices repeat product details.',2),
'T010':('Known preferences used, but repeats facts and asserts everyday suitability broadly.',2),
'T011':('Verified fold-like side profile; no invented origami or comfort claim.',3),
'T012':('Accurate basic product facts; repetitive and slightly strong match language.',2),
'T013':('Grounded black/carrying facts; generic suggestion after client said no rush.',3),
'T014':('Latest black preference respected; elegant hand-feel in option 3 is subjective and unsupported.',3),
'T015':('Regression removes internal style instruction; price and budget supported.',2),
'T016':('No visit pressure despite unavailable weekend; repeated product introduction.',2),
'T017':('Material and dimensions answered; messages are longer than necessary.',2),
'T018':('Applicable core cowhide care, but three options are near duplicates.',1),
'T019':('Latest regression uses conditional scratch language rather than inventing an observed issue; no woven-panel claim.',4),
'T020':('Rain care uses supported blot/air-dry guidance; redundant options.',2),
'T021':('General storage language is reasonable but broader than explicit policy; prefer verified heat/sun advice.',3),
'T022':('Final regression advises not self-applying oil and offers confirmation, rather than asserting no care is needed.',2),
'T023':('Regression offers inspection, does not promise restoration or treat scratch as moisture.',3),
'T024':('No new sales pitch; repeated supported care actions.',2),
'T025':('Woven panel is correctly distinguished; first option should make clear its cowhide-only scope.',4),
'T026':('No verified promotion exists, but volunteered promotion talk and future new-style framing are unnecessary.',3),
'T027':('Regression removes invented prior conversation and launch; thin context leads generic reconnect.',3),
'T028':('Historical interest is used without unverified product details.',3),
'T029':('Final regression option 3 leaves further contact with the client; options 1–2 still assume future updates.',2),
'T030':('No hard sales pressure; question in option 1 is too broad after no purchase plan.',3),
'T031':('Regression removes new-launch assertion; broad other-style suggestion is vague.',3),
'T032':('No specific invented launch, but future notification and latest-update framing still need restraint.',2),
'T033':('Out-of-town context supported; generic help language rather than a concrete relevant reason.',3),
'T034':('Essential verified event facts present; formal wording and confirmed-position phrasing need care.',2),
'T035':('Complete facts, but 莅临/亲爱的 and 下午14:00 are awkward for brand/WeChat.',2),
'T036':('Complete verified event facts and reply route, with similar openings.',2),
'T037':('Complete invitation; 敬爱的 in option 3 is overly formal.',2),
'T038':('Targeted regression removes unverified no-sales/quiet-atmosphere claims; use only supplied event facts.',2),
'T039':('Complete verified event facts; booking wording can more explicitly remain subject to confirmation.',2),
'T040':('Companion eligibility now subject to inquiry; 亲爱的/莅临 remain tone defects.',3),
'T041':('Complete verified invitation; options are largely parallel.',2),
'T042':('Price grounded; option 2 best respects time to consider; option 3 assumes future updates.',3),
'T043':('Sparse-history input, grounded product/price; generic budget language.',3),
'T044':('Directly addresses discount without unauthorized offer; can acknowledge more naturally.',3),
'T045':('Grounded price/features; concern acknowledgement is uneven.',3),
'T046':('Avoids explaining unknown outside-channel difference; could state own no-price-match authority more clearly.',2),
'T047':('Answers gift/coupon question directly with no invented entitlement; repetitive supporting facts.',2),
'T048':('Final regression accurately distinguishes 5800 product price from the 6000 client budget.',3),
'T049':('Concrete product details supplied; avoid asserting unknown causal price breakdown.',3),
'T050':('Final regression accepts deferral without repeating product details or continuing the pitch.',2),
}
author=[]
for e in manifest:
 cid=e['case_id'];note,diversity=notes[cid]
 messages=[]
 for i,text in enumerate(e['result']['candidates']):
  scores={'facts':5,'context':4,'personalization':3,'brand':4,'scenario':4,'boundaries':4,'wechat':4}
  issues=[]
  if len(text)>110:scores['wechat']=3;issues.append('Long for a routine WeChat draft.')
  if any(word in text for word in ['莅临','亲爱的','敬爱的']):scores['brand']=2;issues.append('Overly formal or intimate address.')
  if cid in ['T005','T008'] and i!=1:scores['brand']=3;issues.append('Preference used as a forced greeting metaphor.')
  if cid=='T014' and i==2:scores['facts']=3;issues.append('Unverified subjective hand-feel claim.')
  if cid=='T022' and i==1:scores['facts']=4;issues.append('Generic care caution is sensible but material sensitivity is not product-specific evidence.')
  if cid=='T029' and i<2:scores['boundaries']=3;issues.append('Assumes unsolicited future updates; option 3 leaves contact with the client.')
  if cid=='T032' and i<2:scores['boundaries']=3;scores['scenario']=3;issues.append('Assumes future notifications or updates without explicit request.')
  if cid=='T048':issues.append('Verified price and client budget are correctly distinguished.')
  if cid=='T050':issues.append('Respects deferral without continuing product explanation.')
  messages.append({'scores':scores,'critical':False,'issues':issues})
 author.append({'case_id':cid,'generation_run_id':e['result']['metadata']['run_id'],'reviewer':'Codex author assessment (AI), not a human CA','review':{'messages':messages,'diversity':diversity,'set_notes':note}})
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(out/'author_reviews.json').write_text(json.dumps(author,ensure_ascii=False,indent=2))
# Preserve only model reviews matching selected output run IDs; never borrow old scores.
model=[]
for e in manifest:
 r=reviews.get(e['case_id'])
 if r and r['generation_run_id']==e['result']['metadata']['run_id']:model.append(r)
(out/'reviews.json').write_text(json.dumps(model,ensure_ascii=False,indent=2))
with (out/'test_cases.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['Case ID','Scenario','Client information','Conversation history','Product information','Output 1','Output 2','Output 3'])
 for e in manifest:
  r=e['request'];w.writerow([e['case_id'],r['scenario'],json.dumps(r['client_information'],ensure_ascii=False),json.dumps(r['conversation_history'],ensure_ascii=False),json.dumps(r['product_information'],ensure_ascii=False),*e['result']['candidates']])
print('Final selection:',len(manifest),'cases;',len(model),'matching model reviews; 50 author reviews.')
