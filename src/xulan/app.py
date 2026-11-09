import json
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .budget import BudgetGuard
from .client import OpenAIClient
from .models import GenerationRequest
from .service import CATALOGUE, ROOT, SCENARIOS, ConversationService
from .settings import load_credentials

load_credentials()
app = FastAPI(title='XULAN Advisor Studio')
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
budget = BudgetGuard(ROOT / 'runs/budget.sqlite')
service = ConversationService(OpenAIClient(budget))


@app.get('/')
def home():
    return FileResponse(ROOT / 'static/index.html')


@app.get('/api/health')
def health():
    return {'ready': True, 'credential_configured': bool(os.getenv('OPENAI_API_KEY')), 'budget': budget.summary()}


@app.get('/api/config')
def config():
    return {'brand': '序岚 XULAN', 'fictional': True, 'scenarios': SCENARIOS, 'products': CATALOGUE['products']}


@app.get('/api/clients')
def clients():
    return json.loads((ROOT / 'data/clients.json').read_text())


@app.get('/api/events')
def events():
    return json.loads((ROOT / 'data/events.json').read_text())


@app.get('/api/examples')
def examples():
    return json.loads((ROOT / 'fixtures/examples.json').read_text())


@app.post('/api/generate')
def generate(request: GenerationRequest):
    return service.generate(request)
