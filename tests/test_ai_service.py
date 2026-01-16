"""Unit tests for AI service."""
import unittest
from iterminal.services.ai_service import AIService
from iterminal.interfaces.ai_provider import AIProvider


class MockAIProvider(AIProvider):
    """Mock AI provider for testing."""
    
    def __init__(self, name: str, available: bool = True):
        self._name = name
        self._available = available
    
    def generate_response(self, prompt: str, system: str = None, **kwargs) -> str:
        return f"Mock response to: {prompt}"
    
    def is_available(self) -> bool:
        return self._available
    
    def get_models(self) -> list:
        return ["mock-model-1", "mock-model-2"]
    
    def get_name(self) -> str:
        return self._name


class TestAIService(unittest.TestCase):
    """Test cases for AIService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = AIService()
    
    def test_register_provider(self):
        """Test provider registration."""
        provider = MockAIProvider("test-provider")
        self.service.register_provider(provider)
        
        self.assertIn("test-provider", self.service.list_providers())
    
    def test_set_provider(self):
        """Test setting active provider."""
        provider1 = MockAIProvider("provider-1")
        provider2 = MockAIProvider("provider-2")
        
        self.service.register_provider(provider1)
        self.service.register_provider(provider2)
        
        self.assertTrue(self.service.set_provider("provider-2"))
        self.assertEqual(self.service.get_current_provider().get_name(), "provider-2")
    
    def test_generate_response(self):
        """Test response generation."""
        provider = MockAIProvider("test-provider")
        self.service.register_provider(provider)
        
        response = self.service.generate_response("test prompt")
        self.assertIsNotNone(response)
        self.assertIn("test prompt", response)
    
    def test_unavailable_provider(self):
        """Test handling of unavailable provider."""
        provider = MockAIProvider("unavailable", available=False)
        self.service.register_provider(provider)
        
        self.assertFalse(self.service.set_provider("unavailable"))
    
    def test_available_providers(self):
        """Test listing available providers."""
        provider1 = MockAIProvider("available-1", available=True)
        provider2 = MockAIProvider("unavailable", available=False)
        
        self.service.register_provider(provider1)
        self.service.register_provider(provider2)
        
        available = self.service.get_available_providers()
        self.assertIn("available-1", available)
        self.assertNotIn("unavailable", available)


if __name__ == '__main__':
    unittest.main()
