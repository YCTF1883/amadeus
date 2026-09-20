import json
import unittest

from backend.app.services.sse_service import encode_sse_event


class SseServiceTests(unittest.TestCase):
    def test_text_event_encodes_multiline_content_as_one_json_payload(self):
        encoded = encode_sse_event("text", content="第一行\n第二行")

        self.assertTrue(encoded.startswith("data: "))
        self.assertTrue(encoded.endswith("\n\n"))
        payload = json.loads(encoded.removeprefix("data: ").strip())
        self.assertEqual(payload, {"type": "text", "content": "第一行\n第二行"})


if __name__ == "__main__":
    unittest.main()
