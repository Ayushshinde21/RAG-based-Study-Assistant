import unittest
from unittest import mock

import requests

from utils.http_retry import post_with_retry, provider_max_workers


class FakeResponse:
    def __init__(self, status_code, headers=None, text=""):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text


class TestPostWithRetry(unittest.TestCase):
    @mock.patch("utils.http_retry.time.sleep")
    @mock.patch("utils.http_retry.requests.post")
    def test_retries_transient_server_error(self, post, sleep):
        expected = FakeResponse(200)
        post.side_effect = [FakeResponse(503), expected]

        result = post_with_retry("https://example.test", timeout=(5, 30))

        self.assertIs(result, expected)
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args.kwargs["timeout"], (5, 30))
        sleep.assert_called_once_with(1.0)

    @mock.patch("utils.http_retry.time.sleep")
    @mock.patch("utils.http_retry.requests.post")
    def test_honors_numeric_retry_after_header(self, post, sleep):
        expected = FakeResponse(200)
        post.side_effect = [
            FakeResponse(429, headers={"Retry-After": "4"}),
            expected,
        ]

        result = post_with_retry("https://example.test")

        self.assertIs(result, expected)
        sleep.assert_called_once_with(4.0)

    @mock.patch("utils.http_retry.time.sleep")
    @mock.patch("utils.http_retry.requests.post")
    def test_retries_connection_timeout(self, post, sleep):
        expected = FakeResponse(200)
        post.side_effect = [requests.Timeout("temporary timeout"), expected]

        result = post_with_retry("https://example.test")

        self.assertIs(result, expected)
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(1.0)

    @mock.patch("utils.http_retry.time.sleep")
    @mock.patch("utils.http_retry.requests.post")
    def test_does_not_retry_non_transient_client_error(self, post, sleep):
        expected = FakeResponse(400, text="bad request")
        post.return_value = expected

        result = post_with_retry("https://example.test")

        self.assertIs(result, expected)
        post.assert_called_once()
        sleep.assert_not_called()

    @mock.patch("utils.http_retry.time.sleep")
    @mock.patch("utils.http_retry.requests.post")
    def test_reraises_timeout_after_final_attempt(self, post, sleep):
        post.side_effect = requests.Timeout("provider timeout")

        with self.assertRaisesRegex(requests.Timeout, "provider timeout"):
            post_with_retry("https://example.test", max_attempts=2)

        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(1.0)

    def test_provider_worker_count_is_bounded_and_configurable(self):
        with mock.patch.dict("os.environ", {"SARVAM_MAX_WORKERS": "5"}):
            self.assertEqual(provider_max_workers(), 5)
        with mock.patch.dict("os.environ", {"SARVAM_MAX_WORKERS": "100"}):
            self.assertEqual(provider_max_workers(), 8)
        with mock.patch.dict("os.environ", {"SARVAM_MAX_WORKERS": "invalid"}):
            self.assertEqual(provider_max_workers(), 3)


if __name__ == "__main__":
    unittest.main()
