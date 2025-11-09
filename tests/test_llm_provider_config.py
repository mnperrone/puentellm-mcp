"""
Test cases for LLM provider configuration in llm_config_window.py
"""
import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the LLMConfigWindow class
from llm_config_window import LLMConfigWindow

class TestLLMProviderConfig(unittest.TestCase):
    """Test cases for LLM provider configuration"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test config
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'app_config.json')
        
        # Mock AppConfig
        self.mock_app_config = MagicMock()
        self.mock_app_config.config = {
            'llm_provider': 'ollama',
            'llm_model': 'llama2',
            'llm_provider_configs': {
                'ollama': {
                    'api_key': 'ollama_test_key',
                    'base_url': 'http://localhost:11434',
                    'model': 'llama2'
                }
            },
            'sanitize_model_output': True,
            'auto_space_model_output': False
        }
        self.mock_app_config.config_path = self.config_path
        
        # Save the initial config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.mock_app_config.config, f, indent=4)
        
        # Mock the parent window
        self.mock_parent = MagicMock()
        
        # Patch the AppConfig class to return our mock
        self.app_config_patcher = patch('llm_config_window.AppConfig', return_value=self.mock_app_config)
        self.mock_app_config_class = self.app_config_patcher.start()
        
        # Create the config window
        self.config_window = LLMConfigWindow(self.mock_parent)
        
        # Mock UI elements
        self.config_window.provider_var = MagicMock()
        self.config_window.provider_var.get.return_value = 'openrouter'
        
        self.config_window.model_var = MagicMock()
        self.config_window.model_var.get.return_value = 'mistralai/mistral-7b-instruct:free'
        
        self.config_window.api_key_entry = MagicMock()
        self.config_window.api_key_entry.get.return_value = 'test_openrouter_api_key_123'
        
        self.config_window.base_url_entry = MagicMock()
        self.config_window.base_url_entry.get.return_value = 'https://openrouter.ai/api/v1'
        
        self.config_window.auto_space_var = MagicMock()
        self.config_window.auto_space_var.get.return_value = True
        
        # Mock messagebox to prevent UI popups during tests
        self.messagebox_patcher = patch('llm_config_window.messagebox')
        self.mock_messagebox = self.messagebox_patcher.start()
        
        # Mock the model loading
        self.config_window.load_models = MagicMock(return_value=True)
    
    def tearDown(self):
        """Clean up after tests"""
        self.app_config_patcher.stop()
        self.messagebox_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_save_new_provider_config(self):
        """Test saving a new provider configuration"""
        # Call save_config
        self.config_window.save_config()
        
        # Verify the config was updated correctly
        updated_config = self.mock_app_config.config
        
        # Check top-level provider and model
        self.assertEqual(updated_config['llm_provider'], 'openrouter')
        self.assertEqual(updated_config['llm_model'], 'mistralai/mistral-7b-instruct:free')
        
        # Check provider config was added
        self.assertIn('llm_provider_configs', updated_config)
        self.assertIn('openrouter', updated_config['llm_provider_configs'])
        
        # Check provider config values
        provider_config = updated_config['llm_provider_configs']['openrouter']
        self.assertEqual(provider_config['api_key'], 'test_openrouter_api_key_123')
        self.assertEqual(provider_config['base_url'], 'https://openrouter.ai/api/v1')
        self.assertEqual(provider_config['model'], 'mistralai/mistral-7b-instruct:free')
        
        # Verify no duplicate keys were created
        self.assertNotIn('openrouter_api_key', updated_config)
        self.assertNotIn('openrouter_base_url', updated_config)
        self.assertNotIn('api_key', updated_config)
        self.assertNotIn('base_url', updated_config)
        
        # Verify save_config was called
        self.mock_app_config.save_config.assert_called_once()
    
    def test_duplicate_keys_cleanup(self):
        """Test that duplicate keys are properly cleaned up"""
        # Add some duplicate keys to the config
        self.mock_app_config.config.update({
            'openrouter_api_key': 'duplicate_key',
            'openrouter_base_url': 'https://duplicate.url',
            'api_key': 'another_duplicate',
            'base_url': 'https://another.duplicate'
        })
        
        # Call save_config
        self.config_window.save_config()
        
        # Get the updated config
        updated_config = self.mock_app_config.config
        
        # Verify the duplicates were removed
        self.assertNotIn('openrouter_api_key', updated_config)
        self.assertNotIn('openrouter_base_url', updated_config)
        self.assertNotIn('api_key', updated_config)
        self.assertNotIn('base_url', updated_config)
        
        # Verify the provider config is still correct
        self.assertIn('llm_provider_configs', updated_config)
        self.assertIn('openrouter', updated_config['llm_provider_configs'])
        provider_config = updated_config['llm_provider_configs']['openrouter']
        self.assertEqual(provider_config['api_key'], 'test_openrouter_api_key_123')
        self.assertEqual(provider_config['base_url'], 'https://openrouter.ai/api/v1')
    
    def test_empty_config_initialization(self):
        """Test that the config window works with an empty config"""
        # Create a new empty config
        self.mock_app_config.config = {}
        
        # Create a new config window with the empty config
        config_window = LLMConfigWindow(self.mock_parent)
        
        # Verify the provider configs dict was initialized
        self.assertIn('llm_provider_configs', self.mock_app_config.config)
        self.assertEqual(self.mock_app_config.config['llm_provider_configs'], {})
        
        # Clean up
        config_window.destroy()

if __name__ == '__main__':
    unittest.main()
