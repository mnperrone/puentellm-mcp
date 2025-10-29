"""simulate_stream_events.py
Small harness to simulate structured streaming events the LLMBridge now emits.
Run with: python scripts\simulate_stream_events.py

It prints the chat buffer after each event so you can verify no duplication occurs.
"""

class MockChatDisplay:
    def __init__(self):
        self.buffer = []
        self.tags = set()
    def tag_names(self):
        return list(self.tags)
    def tag_config(self, name, **kwargs):
        self.tags.add(name)
    def insert(self, pos, text, tag=None):
        # We'll ignore pos and tag, just append to buffer
        self.buffer.append(text)
    def configure(self, **kwargs):
        pass
    def see(self, pos):
        pass
    def index(self, idx):
        return str(len(''.join(self.buffer)))
    def delete(self, start, end):
        # not used in this harness
        pass

class Simulator:
    def __init__(self):
        self.chat_display = MockChatDisplay()
        self._assistant_streaming_active = False
        self.assistant_response_active = False

    def process_event(self, event):
        """Mimics the logic in chat_app._process_llm_response for structured events."""
        # Structured dict events: {"content":..., "final": bool}
        is_struct = isinstance(event, dict)
        if is_struct:
            content = event.get('content','')
            final = bool(event.get('final', False))
            if not getattr(self, '_assistant_streaming_active', False):
                self._assistant_streaming_active = True
                self.chat_display.insert('end', 'Asistente: ')
                if content:
                    self.chat_display.insert('end', content)
            else:
                if content:
                    self.chat_display.insert('end', content)
            if final:
                self.chat_display.insert('end', '\n\n')
                self._assistant_streaming_active = False
                self.assistant_response_active = False
        else:
            # Legacy full-string response
            resp = str(event)
            self.assistant_response_active = False
            self.chat_display.insert('end', 'Asistente: ')
            self.chat_display.insert('end', resp)
            self.chat_display.insert('end', '\n\n')

    def get_buffer(self):
        return ''.join(self.chat_display.buffer)


def run_cases():
    sim = Simulator()
    print('Case 1: Streamed chunks then final')
    events = [
        {"content": "Hello ", "final": False},
        {"content": "world!", "final": False},
        {"content": "", "final": True}
    ]
    for i, e in enumerate(events, 1):
        sim.process_event(e)
        print(f'After event {i}:')
        print(repr(sim.get_buffer()))
    print('\nExpected: "Asistente: Hello world!\\n\\n"')

    print('\nCase 2: Non-streaming full response')
    sim2 = Simulator()
    sim2.process_event('This is a full response from the model.')
    print(repr(sim2.get_buffer()))
    print('\nExpected: "Asistente: This is a full response from the model.\\n\\n"')


if __name__ == "__main__":
    run_cases()
