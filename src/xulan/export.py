"""Eight-column submission export (requirement 1.3, section 6).

Scenario facts needed to judge an output are written inside the eight columns:
event facts go into Product information; non-product task facts (occasion, budget,
reference time) go into Conversation history as a labelled "CA task context" block.
"""

import csv
import json
from pathlib import Path

COLUMNS = [
    'Case ID',
    'Scenario',
    'Client information',
    'Conversation history',
    'Product information',
    'Output 1',
    'Output 2',
    'Output 3',
]
EVENT_FIELDS = ('title', 'start', 'end', 'location', 'content', 'booking_route')
TASK_LABELS = {
    'occasion': 'Occasion',
    'occasion_date': 'Occasion date',
    'hard_budget_cny': 'Hard budget (CNY)',
    'required_device_fit': 'Required device fit',
    'verified_device_fit': 'Verified device fit',
}


def spreadsheet_safe(text: str) -> str:
    """Prefix only cells starting with a formula trigger; everything else is unmodified."""
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text


def client_cell(client: dict) -> str:
    return json.dumps({k: v for k, v in client.items() if v not in (None, '')}, ensure_ascii=False)


def history_cell(request: dict) -> str:
    details = request.get('scenario_details') or {}
    lines = ['[CA task context — not a client message]', f'Reference time: {request["current_datetime"]}']
    for key, label in TASK_LABELS.items():
        if details.get(key) not in (None, ''):
            lines.append(f'{label}: {details[key]}')
    lines.append('[Conversation]')
    history = request.get('conversation_history') or []
    if history:
        lines += [f'{h["role"]}: {h["content"]}' for h in history]
    else:
        lines.append('(no prior messages)')
    return '\n'.join(lines)


def product_cell(request: dict, catalogue: dict) -> str:
    details = request.get('scenario_details') or {}
    parts = []
    skus = request.get('product_information') or []
    for p in catalogue['products']:
        if p['sku'] in skus:
            parts.append(
                f'[Product] {p["sku"]} {p["name"]} · ¥{p["price_minor"] // 100:,} · '
                f'{p["material"]} · {p["dimensions_cm"]} cm · {p["design"]}'
            )
    if all(details.get(f) for f in ('title', 'start', 'location')):
        event = ' · '.join(f'{f}: {details[f]}' for f in EVENT_FIELDS if details.get(f))
        parts.append(f'[Event] {event}')
    return '\n'.join(parts) if parts else 'Not applicable'


def case_row(case_id: str, request: dict, candidates: list[str], catalogue: dict) -> list[str]:
    row = [
        case_id,
        request['scenario'],
        client_cell(request['client_information']),
        history_cell(request),
        product_cell(request, catalogue),
        *candidates,
    ]
    return [spreadsheet_safe(str(x)) for x in row]


def result_outputs(result: dict) -> list[str]:
    """Three output cells for any result state; non-success states are labelled, never filled with text."""
    if result['status'] == 'success':
        return list(result['candidates'])
    reasons = (
        result.get('validation_findings') or result.get('blocking_reasons') or result.get('information_requests') or []
    )
    cell = f'[No draft — status: {result["status"]}] ' + ' | '.join(reasons)
    return [cell] * 3


def write_cases_csv(path: Path, rows: list[list[str]]) -> None:
    with Path(path).open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
