import os
import sys
import traceback

# Ensure repo root is in sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from app_config import AppConfig
from llm_bridge import LLMBridge

cfg = AppConfig()
provider = cfg.get('llm_provider')
model = cfg.get('llm_model')
provider_configs = cfg.get('llm_provider_configs', {})
provider_conf = provider_configs.get(provider, {})
api_key = provider_conf.get('api_key') or cfg.get(f'{provider}_api_key')
base_url = provider_conf.get('base_url') or cfg.get(f'{provider}_base_url')
print('Config: provider=', provider, 'model=', model, 'api_key=', '***' if api_key else None, 'base_url=', base_url)
try:
    bridge = LLMBridge(model=model, chat_text=None, window=None, provider=provider, api_key=api_key, base_url=base_url)
    print('LLMBridge initialized. Handler:', type(bridge.handler))
    # Try listing models if handler provides it
    try:
        models = bridge.list_models()
        print('list_models result:', models)
    except Exception as e:
        print('list_models failed:', e)
except Exception as e:
    print('Exception while initializing LLMBridge:')
    traceback.print_exc()
