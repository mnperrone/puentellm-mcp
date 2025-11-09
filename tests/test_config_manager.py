"""
Test cases for the configuration management functionality.
This tests the core configuration logic without the UI components.
"""
import unittest
import os
import json
import tempfile
import shutil
import sys
from unittest.mock import patch, MagicMock, PropertyMock

# Import the AppConfig class
from app_config import AppConfig

class TestConfigManager(unittest.TestCase):
    """Test cases for configuration management"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test config
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'app_config.json')
        
        # Create a test config file
        self.test_config = {
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
        
        # Save the test config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_config, f, indent=4)
        
        # Patch the AppConfig to use our test config path
        self.config_patcher = patch('app_config.AppConfig')
        self.mock_app_config_class = self.config_patcher.start()
        
        # Create a mock instance with our test config
        self.mock_config = MagicMock()
        self.mock_config.config = self.test_config.copy()
        self.mock_config.config_path = self.config_path
        
        # Set up the mock to return our mock instance
        self.mock_app_config_class.return_value = self.mock_config
        
        # Create a test instance of AppConfig
        self.config = AppConfig()
        # Override the config with our test config
        self.config.config = self.test_config.copy()
        self.config.config_path = self.config_path
    
    def tearDown(self):
        """Clean up after tests"""
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_add_new_provider(self):
        """Test adding a new provider configuration"""
        # Add a new provider
        new_provider = 'openrouter'
        provider_config = {
            'api_key': 'test_openrouter_key',
            'base_url': 'https://openrouter.ai/api/v1',
            'model': 'mistralai/mistral-7b-instruct:free'
        }
        
        # Save the new provider config
        if 'llm_provider_configs' not in self.config.config:
            self.config.config['llm_provider_configs'] = {}
        
        self.config.config['llm_provider_configs'][new_provider] = provider_config
        self.config.save_config()
        
        # Reload the config to verify
        with open(self.config_path, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        
        # Verify the provider was added
        self.assertIn('llm_provider_configs', saved_config)
        self.assertIn(new_provider, saved_config['llm_provider_configs'])
        self.assertEqual(
            saved_config['llm_provider_configs'][new_provider],
            provider_config
        )
    
    def test_no_duplicate_keys(self):
        """Test that saving doesn't create duplicate keys"""
        # Add some duplicate keys
        self.config.config.update({
            'openrouter_api_key': 'duplicate_key',
            'openrouter_base_url': 'https://duplicate.url',
            'api_key': 'another_duplicate',
            'base_url': 'https://another.duplicate'
        })
        
        # Save the config
        self.config.save_config()
        
        # Reload the config
        with open(self.config_path, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        
        # Check that the duplicates were removed
        redundant_keys = [
            'openrouter_api_key', 'openrouter_base_url',
            'api_key', 'base_url', 'model'
        ]
        
        for key in redundant_keys:
            self.assertNotIn(key, saved_config)
    
    def test_update_existing_provider(self):
        """Test updating an existing provider's configuration"""
        # Update the existing ollama config
        updated_config = {
            'api_key': 'updated_ollama_key',
            'base_url': 'http://localhost:11435',
            'model': 'llama2:latest'
        }
        
        self.config.config['llm_provider_configs']['ollama'].update(updated_config)
        self.config.save_config()
        
        # Reload the config to verify
        with open(self.config_path, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        
        # Verify the update
        self.assertEqual(
            saved_config['llm_provider_configs']['ollama'],
            updated_config
        )

if __name__ == '__main__':
    unittest.main()
