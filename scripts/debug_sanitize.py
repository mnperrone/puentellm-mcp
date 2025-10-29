from llm_providers.openrouter_handler import OpenRouterHandler
import os
s = ("¡Hola! Soy**DeepSeek-V3**, unmodelo de lenguajeartificial desarrollado por**DeepSeek**. "
            "Estoy aquípara ayudartecon cualquier consultaque tengas,ya sea sobre conocimientosgenerales,"
            "resolución de problemas, consejos ymás.¿Enqué puedo ayudarte hoy?")

h = OpenRouterHandler(api_key='dummy', base_url='https://openrouter.ai/api/v1', model='test-model', verify_on_init=False)
print('ORIGINAL:', s)
print('\n--- sanitized default ---')
print(h._sanitize_text(s))
print('\n--- sanitized with env ---')
os.environ['PUENTE_ENABLE_AUTO_SPACING']='1'
print(h._sanitize_text(s))
