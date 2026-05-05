import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.human_behavior import (
    _bezier,
    _bezier_path,
    human_move_and_click,
    human_type,
    human_scroll,
    human_pre_action_pause,
)


def test_bezier_at_t0_returns_start():
    p0, p1, p2, p3 = (0, 0), (1, 0), (2, 0), (3, 0)
    x, y = _bezier(0.0, p0, p1, p2, p3)
    assert abs(x - 0.0) < 0.001
    assert abs(y - 0.0) < 0.001


def test_bezier_at_t1_returns_end():
    p0, p1, p2, p3 = (0, 0), (1, 0), (2, 0), (10, 5)
    x, y = _bezier(1.0, p0, p1, p2, p3)
    assert abs(x - 10.0) < 0.001
    assert abs(y - 5.0) < 0.001


def test_bezier_at_t05_is_between_start_and_end():
    p0, p1, p2, p3 = (0, 0), (5, 0), (5, 10), (10, 10)
    x, y = _bezier(0.5, p0, p1, p2, p3)
    assert 0 < x < 10
    assert 0 < y < 10


def test_bezier_path_length():
    path = _bezier_path((0, 0), (100, 100), steps=20)
    assert len(path) == 21


def test_bezier_path_starts_near_start():
    path = _bezier_path((10, 20), (100, 200), steps=20)
    x, y = path[0]
    assert abs(x - 10) < 0.001
    assert abs(y - 20) < 0.001


def test_bezier_path_ends_near_end():
    path = _bezier_path((10, 20), (100, 200), steps=20)
    x, y = path[-1]
    assert abs(x - 100) < 0.001
    assert abs(y - 200) < 0.001


@pytest.mark.asyncio
async def test_human_move_and_click_calls_mouse_move_multiple_times():
    page = MagicMock()
    page.evaluate = AsyncMock(return_value={"x": 0, "y": 0})
    page.mouse = MagicMock()
    page.mouse.move = AsyncMock()
    page.mouse.down = AsyncMock()
    page.mouse.up = AsyncMock()

    await human_move_and_click(page, 200, 300)

    assert page.mouse.move.call_count > 5
    page.mouse.down.assert_called_once()
    page.mouse.up.assert_called_once()


@pytest.mark.asyncio
async def test_human_move_and_click_ends_near_target():
    page = MagicMock()
    page.evaluate = AsyncMock(return_value={"x": 0, "y": 0})
    page.mouse = MagicMock()
    page.mouse.move = AsyncMock()
    page.mouse.down = AsyncMock()
    page.mouse.up = AsyncMock()

    await human_move_and_click(page, 500, 400)

    last_call = page.mouse.move.call_args_list[-1]
    x, y = last_call.args[0], last_call.args[1]
    assert abs(x - 500) <= 5
    assert abs(y - 400) <= 5


@pytest.mark.asyncio
async def test_human_type_calls_keyboard_type_for_each_char():
    page = MagicMock()
    page.keyboard = MagicMock()
    page.keyboard.type = AsyncMock()
    page.keyboard.press = AsyncMock()

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await human_type(page, "hello")

    assert page.keyboard.type.call_count >= 5


@pytest.mark.asyncio
async def test_human_type_types_correct_final_text():
    page = MagicMock()
    typed_chars: list[str] = []

    async def fake_type(char):
        typed_chars.append(char)

    async def fake_press(key):
        if key == "Backspace" and typed_chars:
            typed_chars.pop()

    page.keyboard = MagicMock()
    page.keyboard.type = fake_type
    page.keyboard.press = fake_press

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with patch("random.random", return_value=1.0):  # no typos
            await human_type(page, "test")

    assert "".join(typed_chars) == "test"


@pytest.mark.asyncio
async def test_human_type_introduces_delays():
    page = MagicMock()
    page.keyboard = MagicMock()
    page.keyboard.type = AsyncMock()
    page.keyboard.press = AsyncMock()

    sleep_calls: list[float] = []

    async def fake_sleep(t):
        sleep_calls.append(t)

    with patch("asyncio.sleep", fake_sleep):
        with patch("random.random", return_value=1.0):
            await human_type(page, "ab")

    assert len(sleep_calls) >= 2
    assert all(t >= 0.02 for t in sleep_calls)


@pytest.mark.asyncio
async def test_human_scroll_calls_wheel_multiple_times():
    page = MagicMock()
    page.mouse = MagicMock()
    page.mouse.wheel = AsyncMock()

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await human_scroll(page, "down", 400)

    assert page.mouse.wheel.call_count >= 3


@pytest.mark.asyncio
async def test_human_scroll_down_uses_positive_delta():
    page = MagicMock()
    page.mouse = MagicMock()
    wheel_calls: list[tuple] = []

    async def fake_wheel(dx, dy):
        wheel_calls.append((dx, dy))

    page.mouse.wheel = fake_wheel

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await human_scroll(page, "down", 400)

    assert all(dy > 0 for _, dy in wheel_calls)


@pytest.mark.asyncio
async def test_human_scroll_up_uses_negative_delta():
    page = MagicMock()
    page.mouse = MagicMock()
    wheel_calls: list[tuple] = []

    async def fake_wheel(dx, dy):
        wheel_calls.append((dx, dy))

    page.mouse.wheel = fake_wheel

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await human_scroll(page, "up", 400)

    assert all(dy < 0 for _, dy in wheel_calls)


@pytest.mark.asyncio
async def test_human_pre_action_pause_sleeps():
    sleep_calls: list[float] = []

    async def fake_sleep(t):
        sleep_calls.append(t)

    with patch("asyncio.sleep", fake_sleep):
        await human_pre_action_pause()

    assert len(sleep_calls) == 1
    assert 0.2 <= sleep_calls[0] <= 0.8
