# Contributing to BrowserPilot

Thanks for your interest in contributing! Here's how to get started.

## Setup

```bash
git clone https://github.com/ai-naymul/BrowserPilot.git
cd BrowserPilot
pip install -r requirements.txt
playwright install chromium
```

## Development Workflow

1. Fork the repo and create a feature branch
2. Make your changes
3. Run tests: `python -m pytest tests/ -v`
4. Commit with a clear message
5. Open a pull request

## Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Single file
python -m pytest tests/test_proxy_manager.py -v

# Single test
python -m pytest tests/test_proxy_manager.py::TestProxyInfo::test_default_values -v
```

## Guidelines

- Add tests for new functionality
- Don't break existing tests
- Keep commits focused and atomic
- Use descriptive commit messages

## Reporting Bugs

Use the [bug report template](https://github.com/ai-naymul/BrowserPilot/issues/new?template=bug_report.md) to file issues.

## Feature Requests

Use the [feature request template](https://github.com/ai-naymul/BrowserPilot/issues/new?template=feature_request.md) to suggest features.
