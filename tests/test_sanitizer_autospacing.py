import os
import unittest
from llm_providers.openrouter_handler import OpenRouterHandler

class TestSanitizerAutoSpacing(unittest.TestCase):
    def setUp(self):
        # Create a handler with dummy key (we won't call network methods in these tests)
        self.handler = OpenRouterHandler(api_key='dummy', base_url='https://openrouter.ai/api/v1', model='test-model', verify_on_init=False)
        # Problematic sample from user
        self.sample = (
            "¡Hola! Soy**DeepSeek-V3**, unmodelo de lenguajeartificial desarrollado por**DeepSeek**. "
            "Estoy aquípara ayudartecon cualquier consultaque tengas,ya sea sobre conocimientosgenerales,"
            "resolución de problemas, consejos ymás.¿Enqué puedo ayudarte hoy?"
        )

    def test_sanitizer_without_autospacing_leaves_missing_spaces(self):
        # Ensure env var is not set
        if 'PUENTE_ENABLE_AUTO_SPACING' in os.environ:
            del os.environ['PUENTE_ENABLE_AUTO_SPACING']
        out = self.handler._sanitize_text(self.sample)
        # Expect the problematic concatenations to still be present
        self.assertIn('unmodelo', out)
        self.assertIn('lenguajeartificial', out)
        self.assertIn('aquípara', out)
        self.assertIn('ayudartecon', out)
        self.assertIn('consultaque', out)
        self.assertTrue(('tengas, ya' in out) or ('tengas,ya' in out))

    def test_autospacing_env_enables_correction(self):
        os.environ['PUENTE_ENABLE_AUTO_SPACING'] = '1'
        out = self.handler._sanitize_text(self.sample)
        # Now expect corrected boundaries
        self.assertIn('un modelo', out)
        self.assertIn('lenguaje artificial', out)
        self.assertIn('aquí para', out)
        self.assertIn('ayudarte con', out)
        self.assertIn('consulta que', out)
        self.assertIn('tengas, ya', out)
        del os.environ['PUENTE_ENABLE_AUTO_SPACING']

if __name__ == '__main__':
    unittest.main()
