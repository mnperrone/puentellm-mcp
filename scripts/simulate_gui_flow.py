import os
import sys
import time
import json
import traceback

# Ensure repo root in sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from app_config import AppConfig
from llm_bridge import LLMBridge
from llm_providers import get_llm_handler

cfg = AppConfig()
print('Loaded config path:', cfg.config_path)
provider = cfg.get('llm_provider', 'ollama')
model = cfg.get('llm_model', '')
print('Current provider:', provider)
print('Current model:', model)

# Derive api_key/base_url from provider_configs or top-level keys
provider_configs = cfg.get('llm_provider_configs', {})
prov_conf = provider_configs.get(provider, {})
api_key = prov_conf.get('api_key') or cfg.get(f'{provider}_api_key')
base_url = prov_conf.get('base_url') or cfg.get(f'{provider}_base_url')
print('api_key present:', bool(api_key))
print('base_url:', base_url)

print('\n-- TEST CONNECTION (list_models) --')
try:
    bridge = LLMBridge(model=model or '', chat_text=None, window=None, provider=provider, api_key=api_key, base_url=base_url)
    print('LLMBridge handler:', type(bridge.handler))
    models = bridge.list_models()
    print('Found models count:', len(models) if models else 0)
    if models:
        print('Sample models:', models[:5])
except Exception as e:
    print('Test connection failed:', str(e))
    traceback.print_exc()

print('\n-- SAVE CONFIG (simulating Save in UI) --')
try:
    # Prepare config data
    selection = provider
    cfgs = provider_configs.copy()
    cfgs[selection] = {
        'api_key': api_key or '',
        'base_url': base_url or '',
        'model': model or ''
    }
    cfg.set('llm_provider_configs', cfgs)
    # Also write top-level keys for compatibility
    if api_key:
        cfg.set(f'{selection}_api_key', api_key)
    if base_url:
        cfg.set(f'{selection}_base_url', base_url)
    cfg.set('llm_provider', selection)
    cfg.set('llm_model', model or '')
    print('Config saved.')
except Exception as e:
    print('Save config failed:', e)
    traceback.print_exc()

print('\n-- START LLM (simulate start_llm) --')
try:
    # Simulate initialisation similar to ChatApp.init_llm + start_llm
    bridge2 = LLMBridge(model=model or '', chat_text=None, window=None, provider=provider, api_key=api_key, base_url=base_url)
    print('LLMBridge2 initialized, handler type:', type(bridge2.handler))
    # Optionally, try to stream a small request if supported
    try:
        models2 = bridge2.list_models()
        print('list_models again returned', len(models2) if models2 else 0)
    except Exception as e:
        print('list_models on start failed:', e)

    print('Simulated start complete.')
except Exception as e:
    print('Start LLM failed:', str(e))
    traceback.print_exc()

print('\n-- TAIL LOGS --')
import os
from pathlib import Path

# Repo logs
repo_log_dir = Path('logs')
if repo_log_dir.exists():
    files = sorted(repo_log_dir.glob('*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        latest = files[0]
        print('Repo latest log:', latest)
        print(latest.read_text(encoding='utf-8')[-4000:])

# User logs
user_log_dir = Path(os.path.expanduser('~')) / '.puentellm-mcp' / 'logs'
if user_log_dir.exists():
    files = sorted(user_log_dir.glob('*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        latest = files[0]
        print('User latest log:', latest)
        print(latest.read_text(encoding='utf-8')[-4000:])
