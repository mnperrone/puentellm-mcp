import unittest
import time

import llm_bridge as lb

class MockHandler:
    def __init__(self, chunks):
        self.chunks = chunks
    def stream(self, messages):
        # simulate streaming: yield dicts with 'message' -> 'content'
        for c in self.chunks:
            yield {'message': {'content': c}}

class MockWindow:
    def winfo_exists(self):
        return True
    def after(self, delay, func, *args):
        # call immediately for test determinism
        func(*args)

class TestStreamingBehavior(unittest.TestCase):
    def test_llmbridge_stream_events(self):
        # Monkeypatch get_llm_handler inside llm_bridge module by replacing function
        # Save original
        original_get = lb.get_llm_handler
        try:
            def fake_get_llm_handler(provider_name, model=None, api_key=None, base_url=None):
                return MockHandler(["Hello ", "world!"])
            lb.get_llm_handler = fake_get_llm_handler

            # Prepare bridge with mock window and chat_text
            bridge = lb.LLMBridge(model='test-model', chat_text=None, window=MockWindow(), provider='openrouter')

            events = []
            def cb(event):
                events.append(event)

            bridge.process_user_input("hi", "", cb)

            # wait for thread to run
            timeout = time.time() + 2
            while time.time() < timeout:
                if any(isinstance(e, dict) and e.get('final') for e in events):
                    break
                time.sleep(0.01)

            # Expect two chunk events and one final event
            # Events are dicts: {'content': str, 'final': bool} per our LLMBridge implementation
            contents = [e for e in events if isinstance(e, dict)]
            self.assertGreaterEqual(len(contents), 3, f"Expected at least 3 events (2 chunks + final), got {contents}")
            # First two should be chunks with content
            self.assertEqual(contents[0]['content'], 'Hello ')
            self.assertFalse(contents[0]['final'])
            self.assertEqual(contents[1]['content'], 'world!')
            self.assertFalse(contents[1]['final'])
            # Last should be final True
            self.assertTrue(any(e.get('final') for e in contents))
        finally:
            lb.get_llm_handler = original_get

if __name__ == '__main__':
    unittest.main()
