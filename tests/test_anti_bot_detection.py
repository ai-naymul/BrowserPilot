import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.anti_bot_detection import AntiBotVisionModel


@pytest.fixture
def anti_bot_model(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key-for-testing")
    with patch("backend.anti_bot_detection.genai") as mock_genai:
        model = AntiBotVisionModel()
    return model


# --- _parse_fallback_response tests ---

class TestParseFallbackResponse:

    def test_detects_cloudflare(self, anti_bot_model):
        result = anti_bot_model._parse_fallback_response(
            "This page is protected by Cloudflare", "https://example.com"
        )
        assert result["is_anti_bot"] is True
        assert result["detection_type"] == "cloudflare"
        assert result["suggested_action"] == "rotate_proxy"

    def test_detects_captcha(self, anti_bot_model):
        result = anti_bot_model._parse_fallback_response(
            "Please solve the CAPTCHA to continue", "https://example.com"
        )
        assert result["is_anti_bot"] is True
        assert result["detection_type"] == "captcha"
        assert result["can_solve"] is True
        assert result["suggested_action"] == "solve_captcha"

    def test_detects_rate_limit(self, anti_bot_model):
        result = anti_bot_model._parse_fallback_response(
            "You have been rate limited", "https://example.com"
        )
        assert result["is_anti_bot"] is True
        assert "rate limit" in result["detection_type"]

    def test_detects_access_denied(self, anti_bot_model):
        result = anti_bot_model._parse_fallback_response(
            "Access Denied - you are blocked", "https://example.com"
        )
        assert result["is_anti_bot"] is True

    def test_detects_security_check(self, anti_bot_model):
        result = anti_bot_model._parse_fallback_response(
            "Security check in progress", "https://example.com"
        )
        assert result["is_anti_bot"] is True

    def test_no_anti_bot_on_clean_page(self, anti_bot_model):
        result = anti_bot_model._parse_fallback_response(
            "Welcome to our website. Browse our products.", "https://example.com"
        )
        assert result["is_anti_bot"] is False
        assert result["detection_type"] == "none"
        assert result["suggested_action"] == "continue"

    def test_case_insensitive_detection(self, anti_bot_model):
        result = anti_bot_model._parse_fallback_response(
            "CLOUDFLARE PROTECTION ACTIVE", "https://example.com"
        )
        assert result["is_anti_bot"] is True

    def test_multiple_keywords_detected(self, anti_bot_model):
        result = anti_bot_model._parse_fallback_response(
            "Cloudflare captcha verification required", "https://example.com"
        )
        assert result["is_anti_bot"] is True
        assert result["confidence"] == 0.7

    def test_checking_your_browser(self, anti_bot_model):
        result = anti_bot_model._parse_fallback_response(
            "Checking your browser before accessing the site", "https://example.com"
        )
        assert result["is_anti_bot"] is True

    def test_unusual_activity(self, anti_bot_model):
        result = anti_bot_model._parse_fallback_response(
            "We detected unusual activity from your network", "https://example.com"
        )
        assert result["is_anti_bot"] is True


# --- analyze_anti_bot_page tests (mocked API) ---

class TestAnalyzeAntiBotPage:

    @pytest.fixture
    def fake_screenshot_b64(self):
        # 1x1 red PNG pixel in base64
        import base64
        from PIL import Image
        import io
        img = Image.new("RGB", (10, 10), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    async def test_parses_valid_json_response(self, anti_bot_model, fake_screenshot_b64):
        expected = {
            "is_anti_bot": True,
            "detection_type": "cloudflare",
            "confidence": 0.95,
            "description": "Cloudflare challenge page",
            "can_solve": False,
            "suggested_action": "rotate_proxy"
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(expected)
        anti_bot_model.model = MagicMock()
        anti_bot_model.model.generate_content = MagicMock(return_value=mock_response)

        result = await anti_bot_model.analyze_anti_bot_page(
            fake_screenshot_b64, "detect anti-bot", "https://example.com"
        )
        assert result["is_anti_bot"] is True
        assert result["detection_type"] == "cloudflare"

    async def test_parses_json_wrapped_in_text(self, anti_bot_model, fake_screenshot_b64):
        mock_response = MagicMock()
        mock_response.text = 'Here is my analysis:\n{"is_anti_bot": false, "detection_type": "none", "confidence": 0.1}\nDone.'
        anti_bot_model.model = MagicMock()
        anti_bot_model.model.generate_content = MagicMock(return_value=mock_response)

        result = await anti_bot_model.analyze_anti_bot_page(
            fake_screenshot_b64, "detect anti-bot", "https://example.com"
        )
        assert result["is_anti_bot"] is False

    async def test_falls_back_on_invalid_json(self, anti_bot_model, fake_screenshot_b64):
        mock_response = MagicMock()
        mock_response.text = "I see a cloudflare protection page with a captcha"
        anti_bot_model.model = MagicMock()
        anti_bot_model.model.generate_content = MagicMock(return_value=mock_response)

        result = await anti_bot_model.analyze_anti_bot_page(
            fake_screenshot_b64, "detect anti-bot", "https://example.com"
        )
        assert result["is_anti_bot"] is True
        assert result["detection_type"] == "cloudflare"

    async def test_handles_api_error(self, anti_bot_model, fake_screenshot_b64):
        anti_bot_model.model = MagicMock()
        anti_bot_model.model.generate_content = MagicMock(side_effect=Exception("API error"))

        result = await anti_bot_model.analyze_anti_bot_page(
            fake_screenshot_b64, "detect anti-bot", "https://example.com"
        )
        assert result["is_anti_bot"] is False
        assert result["suggested_action"] == "retry"


# --- solve_captcha tests (mocked API) ---

class TestSolveCaptcha:

    @pytest.fixture
    def fake_screenshot_b64(self):
        import base64
        from PIL import Image
        import io
        img = Image.new("RGB", (10, 10), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    async def test_solves_text_captcha(self, anti_bot_model, fake_screenshot_b64):
        expected = {
            "can_solve": True,
            "solution_type": "text",
            "solution": "X7K9M",
            "confidence": 0.85,
            "instructions": "Type X7K9M in the input field"
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(expected)
        anti_bot_model.model = MagicMock()
        anti_bot_model.model.generate_content = MagicMock(return_value=mock_response)

        result = await anti_bot_model.solve_captcha(
            fake_screenshot_b64, "https://example.com", "text"
        )
        assert result["can_solve"] is True
        assert result["solution"] == "X7K9M"

    async def test_returns_failure_on_invalid_response(self, anti_bot_model, fake_screenshot_b64):
        mock_response = MagicMock()
        mock_response.text = "I cannot read this captcha clearly"
        anti_bot_model.model = MagicMock()
        anti_bot_model.model.generate_content = MagicMock(return_value=mock_response)

        result = await anti_bot_model.solve_captcha(
            fake_screenshot_b64, "https://example.com", "text"
        )
        assert result["can_solve"] is False

    async def test_handles_api_error(self, anti_bot_model, fake_screenshot_b64):
        anti_bot_model.model = MagicMock()
        anti_bot_model.model.generate_content = MagicMock(side_effect=Exception("timeout"))

        result = await anti_bot_model.solve_captcha(
            fake_screenshot_b64, "https://example.com", "text"
        )
        assert result["can_solve"] is False
        assert result["solution_type"] == "error"
