import hashlib
import json
import socket
import unittest
from dataclasses import asdict
from unittest.mock import MagicMock, patch

from kuang.local_planner import LOCAL_MODEL, _request, ollama_plan
from kuang.schema import ValidationError
from kuang.song import rules_plan
from test_song import PROMPTS


class LocalPlannerTests(unittest.TestCase):
    def setUp(self):
        self.spec = asdict(rules_plan(PROMPTS[0])[0])
        self.result = {"model": LOCAL_MODEL, "done": True, "done_reason": "stop", "response": json.dumps(self.spec), "eval_count": 200}
        self.tags = {"models": [{"name": LOCAL_MODEL, "digest": "a"*64}]}
        self.info = {"license": "\n Apache License\nVersion 2.0"}

    def request(self, endpoint, payload, deadline):
        return {"tags": self.tags, "show": self.info, "version": {"version": "test"}, "generate": self.result}[endpoint]

    def test_valid_structured_plan_has_local_model_digest_and_honest_provenance(self):
        with patch("kuang.local_planner._request", side_effect=self.request) as request:
            spec, messages, provenance = ollama_plan(PROMPTS[0])
        self.assertEqual(asdict(spec), self.spec)
        self.assertTrue(provenance["ai_plan"])
        self.assertEqual(provenance["model_digest"], "a"*64)
        self.assertEqual(provenance["response_sha256"], hashlib.sha256(self.result["response"].encode()).hexdigest())
        payload = request.call_args_list[-1].args[1]
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])
        self.assertEqual(payload["keep_alive"], 0)
        self.assertFalse(payload["format"]["additionalProperties"])
        self.assertEqual(payload["format"]["properties"]["seed"]["const"], 7)
        self.assertEqual(payload["format"]["properties"]["tonic"]["const"], 9)
        self.assertEqual(payload["format"]["properties"]["bpm"]["const"], 140)
        self.assertEqual(payload["options"]["temperature"], 0)
        self.assertEqual(payload["options"]["num_ctx"], 4096)
        self.assertNotIn("tools", payload)

    def test_invalid_untrusted_json_never_falls_back_or_executes(self):
        invalid = ["```json\n"+json.dumps(self.spec)+"\n```", '{"seed":7,"seed":8}',
                   json.dumps({**self.spec, "command": "touch /tmp/injected"}),
                   json.dumps({**self.spec, "bpm": 900}), json.dumps({**self.spec, "seed": 8}),
                   json.dumps({**self.spec, "tonic": 0}), json.dumps({**self.spec, "instruments": ["bass", "exec"]}),
                   json.dumps({**self.spec, "bpm": float("nan")}), "x"*16385]
        for response in invalid:
            with self.subTest(response=response[:40]):
                self.result["response"] = response
                with patch("kuang.local_planner._request", side_effect=self.request):
                    with self.assertRaises(ValidationError): ollama_plan(PROMPTS[0])

    def test_missing_model_cloud_research_firm_and_bad_licenses_are_rejected(self):
        with patch("kuang.local_planner._request", side_effect=self.request) as request:
            for model in ("firm:4b-v1", "qwen2.5:3b-instruct", "qwen3.5:4b-cloud", "https://remote/model"):
                with self.assertRaises(ValidationError): ollama_plan(PROMPTS[0], model=model)
            request.assert_not_called()
        for tags in ({"models": []}, {"models": [{"name": LOCAL_MODEL, "digest": "a"*64, "remote_host": "https://ollama.com"}]},
                     {"models": [{"name": LOCAL_MODEL, "digest": "invalid"}]}, {"models": "bad"}):
            self.tags = tags
            with patch("kuang.local_planner._request", side_effect=self.request):
                with self.assertRaises(ValidationError): ollama_plan(PROMPTS[0])
        self.tags = {"models": [{"name": LOCAL_MODEL, "digest": "a"*64}]}
        for info in ({"license": "research"}, {"license": "Apache License", "remote_model": "cloud"}):
            self.info = info
            with patch("kuang.local_planner._request", side_effect=self.request):
                with self.assertRaises(ValidationError): ollama_plan(PROMPTS[0])

    def test_incomplete_generation_wrong_model_and_timeout_never_fall_back(self):
        for update in ({"done": False}, {"done_reason": "length"}, {"model": "cloud"}, {"response": None}):
            result = {**self.result, **update}
            with patch("kuang.local_planner._request", side_effect=lambda endpoint, payload, deadline: result if endpoint == "generate" else self.request(endpoint, payload, deadline)):
                with self.assertRaises(ValidationError): ollama_plan(PROMPTS[0])
        for timeout in (-1, float("nan"), 301):
            with self.assertRaises(ValidationError): ollama_plan(PROMPTS[0], timeout=timeout)

    def test_http_is_fixed_loopback_bounded_no_redirect_proxy_or_download(self):
        response = MagicMock(status=200)
        response.isclosed.side_effect = [False, False]
        response.read1.side_effect = [b'{"ok":true}', b'']
        with patch("kuang.local_planner.http.client.HTTPConnection") as connection, patch("kuang.local_planner.time.monotonic", return_value=1):
            connection.return_value.getresponse.return_value = response
            self.assertEqual(_request("generate", {"prompt": "x"}, 11), {"ok": True})
            connection.assert_called_once_with("127.0.0.1", 11434, timeout=10)
            args = connection.return_value.request.call_args
            self.assertEqual(args.args[:2], ("POST", "/api/generate"))
            self.assertEqual(json.loads(args.kwargs["body"]), {"prompt": "x"})
            connection.return_value.close.assert_called_once()
        for status in (302, 500):
            with patch("kuang.local_planner.http.client.HTTPConnection") as connection:
                connection.return_value.getresponse.return_value.status = status
                with self.assertRaisesRegex(ValidationError, "HTTP"):
                    _request("tags", None, 10**12)
        response.isclosed.side_effect = None; response.isclosed.return_value = False
        response.read1.side_effect = None; response.read1.return_value = b'x'*16384
        with patch("kuang.local_planner.http.client.HTTPConnection") as connection:
            connection.return_value.getresponse.return_value = response
            with self.assertRaisesRegex(ValidationError, "oversized"):
                _request("tags", None, 10**12)
        with patch("kuang.local_planner.http.client.HTTPConnection", side_effect=socket.timeout("slow")):
            with self.assertRaises(ValidationError):
                _request("tags", None, 10**12)

    def test_closed_response_and_expired_deadline(self):
        response = MagicMock(status=200)
        response.isclosed.side_effect = [False, True]
        response.read1.return_value = b'{"version":"test"}'
        with patch("kuang.local_planner.http.client.HTTPConnection") as connection:
            connection.return_value.getresponse.return_value = response
            self.assertEqual(_request("version", None, 10**12), {"version": "test"})
        with self.assertRaisesRegex(ValidationError, "timed out"):
            _request("tags", None, 0)
