import json
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field
from typing import Dict

# Mock page_state element
@dataclass
class MockElement:
    tag_name: str = "a"
    text: str = ""
    is_clickable: bool = False
    is_input: bool = False
    attributes: Dict = field(default_factory=dict)

# Mock page_state
@dataclass
class MockPageState:
    url: str = "https://example.com"
    title: str = "Example"
    selector_map: Dict = field(default_factory=dict)


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch genai before importing vision_model since it configures at module level
import unittest.mock
sys.modules["dotenv"] = MagicMock()
with patch.dict(os.environ, {"GOOGLE_API_KEY": "fake-key"}):
    from backend.vision_model import (
        detect_website_type,
        parse_ai_response,
        extract_search_query,
        get_fallback_action,
        extract_token_usage,
    )


class TestDetectWebsiteType:

    def test_google_search_results(self):
        elements = [{"text": "search result"}]
        assert detect_website_type("https://google.com/search?q=test", "test - Google", elements) == "search_results"

    def test_google_homepage(self):
        assert detect_website_type("https://google.com", "Google", []) == "search_engine"

    def test_bing(self):
        assert detect_website_type("https://bing.com/search?q=test", "test - Bing", []) == "search_results"

    def test_amazon(self):
        assert detect_website_type("https://amazon.com/dp/123", "Product", []) == "ecommerce"

    def test_ecommerce_by_title(self):
        assert detect_website_type("https://mysite.com", "My Shop - Buy Now", []) == "ecommerce"

    def test_linkedin(self):
        assert detect_website_type("https://linkedin.com/in/user", "User", []) == "social_profile"

    def test_github(self):
        assert detect_website_type("https://github.com/user", "user - GitHub", []) == "social_profile"

    def test_news_site(self):
        assert detect_website_type("https://site.com/p/1", "Breaking News Today", []) == "content_site"

    def test_company_site(self):
        assert detect_website_type("https://site.com", "About Our Company", []) == "company_site"

    def test_directory_site(self):
        assert detect_website_type("https://site.com/directory", "Listings", []) == "database_site"

    def test_general_fallback(self):
        assert detect_website_type("https://random.io", "Random Page", []) == "general_website"

    def test_form_application(self):
        elements = [
            {"input": True}, {"input": True},
            {"input": True}, {"input": True},
        ]
        assert detect_website_type("https://app.com/form", "Apply", elements) == "form_application"


class TestExtractSearchQuery:

    def test_removes_stop_words(self):
        result = extract_search_query("search for wireless headphones")
        assert "search" not in result.lower()
        assert "for" not in result.lower()
        assert "wireless" in result
        assert "headphones" in result

    def test_limits_query_length(self):
        result = extract_search_query("find the best cheap wireless bluetooth headphones under fifty dollars available now")
        words = result.split()
        assert len(words) <= 6

    def test_simple_goal(self):
        result = extract_search_query("python tutorials")
        assert "python" in result
        assert "tutorials" in result

    def test_removes_action_words(self):
        result = extract_search_query("go to Amazon and get info about laptops")
        assert "go" not in result.split()
        assert "laptops" in result


class TestParseAiResponse:

    def _make_page_state(self, indices=None):
        state = MockPageState()
        if indices:
            for i in indices:
                state.selector_map[i] = MockElement(text=f"Element {i}")
        return state

    def test_parses_valid_json(self):
        state = self._make_page_state([0, 1, 2])
        raw = '{"action": "click", "index": 0, "reason": "test"}'
        result = parse_ai_response(raw, state, "test goal", "general_website")
        assert result["action"] == "click"
        assert result["index"] == 0

    def test_parses_json_wrapped_in_text(self):
        state = self._make_page_state([0])
        raw = 'Here is my decision:\n{"action": "scroll", "direction": "down", "amount": 300, "reason": "explore"}\nDone.'
        result = parse_ai_response(raw, state, "test", "general_website")
        assert result["action"] == "scroll"

    def test_invalid_action_triggers_fallback(self):
        state = self._make_page_state([0])
        raw = '{"action": "fly_away", "reason": "invalid"}'
        result = parse_ai_response(raw, state, "test", "general_website")
        # Should get fallback (scroll down)
        assert result["action"] in ["click", "type", "scroll"]

    def test_invalid_index_triggers_fallback(self):
        state = self._make_page_state([0, 1])
        raw = '{"action": "click", "index": 999, "reason": "bad index"}'
        result = parse_ai_response(raw, state, "test", "general_website")
        assert result.get("index") != 999

    def test_no_json_triggers_fallback(self):
        state = self._make_page_state([0])
        raw = "I think we should scroll down to see more content"
        result = parse_ai_response(raw, state, "test", "general_website")
        assert result["action"] in ["click", "type", "scroll"]

    def test_extract_action(self):
        state = self._make_page_state([])
        raw = '{"action": "extract", "reason": "found data"}'
        result = parse_ai_response(raw, state, "test", "general_website")
        assert result["action"] == "extract"

    def test_done_action(self):
        state = self._make_page_state([])
        raw = '{"action": "done", "reason": "complete"}'
        result = parse_ai_response(raw, state, "test", "general_website")
        assert result["action"] == "done"


class TestGetFallbackAction:

    def test_finds_search_box(self):
        state = MockPageState()
        state.selector_map = {
            0: MockElement(tag_name="input", text="Search", is_input=True,
                          attributes={"placeholder": "Search..."}),
        }
        result = get_fallback_action(state, "search for python tutorials", "general_website")
        assert result["action"] == "type"
        assert result["index"] == 0

    def test_finds_relevant_link(self):
        state = MockPageState()
        state.selector_map = {
            0: MockElement(tag_name="a", text="Python Documentation", is_clickable=True),
            1: MockElement(tag_name="a", text="About Us", is_clickable=True),
        }
        result = get_fallback_action(state, "Python docs", "general_website")
        assert result["action"] == "click"
        assert result["index"] == 0

    def test_search_results_clicks_first_result(self):
        state = MockPageState()
        state.selector_map = {
            0: MockElement(tag_name="a", text="A detailed search result about something", is_clickable=True),
        }
        result = get_fallback_action(state, "anything", "search_results")
        assert result["action"] == "click"

    def test_scrolls_when_nothing_matches(self):
        state = MockPageState()
        state.selector_map = {}
        result = get_fallback_action(state, "something obscure", "general_website")
        assert result["action"] == "scroll"
        assert result["direction"] == "down"


class TestExtractTokenUsage:

    def test_from_usage_metadata(self):
        response = MagicMock()
        response.usage_metadata.prompt_token_count = 100
        response.usage_metadata.candidates_token_count = 50
        response.usage_metadata.total_token_count = 150
        result = extract_token_usage(response)
        assert result["prompt_tokens"] == 100
        assert result["response_tokens"] == 50
        assert result["total_tokens"] == 150

    def test_returns_none_when_no_usage(self):
        response = MagicMock()
        response.usage_metadata = None
        response.result = None
        response.candidates = None
        result = extract_token_usage(response)
        assert result is None

    def test_handles_exception(self):
        response = MagicMock()
        response.usage_metadata = property(lambda self: (_ for _ in ()).throw(Exception("fail")))
        type(response).usage_metadata = property(lambda self: (_ for _ in ()).throw(Exception("fail")))
        result = extract_token_usage(response)
        assert result is None
