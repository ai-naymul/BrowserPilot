import asyncio
import random
from typing import Optional
from playwright.async_api import Page
from backend.config import (
    HUMAN_TYPING_WPM_MIN,
    HUMAN_TYPING_WPM_MAX,
    HUMAN_TYPO_RATE,
    HUMAN_MOUSE_STEPS,
)


def _bezier(t: float, p0: tuple, p1: tuple, p2: tuple, p3: tuple) -> tuple:
    """Cubic Bezier interpolation between four control points at parameter t in [0,1]."""
    mt = 1 - t
    x = mt**3 * p0[0] + 3*mt**2*t * p1[0] + 3*mt*t**2 * p2[0] + t**3 * p3[0]
    y = mt**3 * p0[1] + 3*mt**2*t * p1[1] + 3*mt*t**2 * p2[1] + t**3 * p3[1]
    return (x, y)


def _bezier_path(start: tuple, end: tuple, steps: int) -> list[tuple]:
    """Generate steps+1 points along a cubic Bezier curve from start to end."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    cp1 = (start[0] + dx * 0.3 + random.uniform(-50, 50),
           start[1] + dy * 0.1 + random.uniform(-50, 50))
    cp2 = (start[0] + dx * 0.7 + random.uniform(-50, 50),
           start[1] + dy * 0.9 + random.uniform(-50, 50))
    return [_bezier(i / steps, start, cp1, cp2, end) for i in range(steps + 1)]


async def human_move_and_click(page: Page, x: float, y: float) -> None:
    """Move mouse along a Bezier curve to (x,y) then click with randomised hold duration."""
    current = await page.evaluate("() => ({ x: window._lastMouseX || 0, y: window._lastMouseY || 0 })")
    start = (current.get("x", 0), current.get("y", 0))
    target = (x + random.uniform(-3, 3), y + random.uniform(-3, 3))
    path = _bezier_path(start, target, HUMAN_MOUSE_STEPS)
    for px, py in path:
        await page.mouse.move(px, py)
        await asyncio.sleep(random.uniform(0.005, 0.025))
    hold_s = random.randint(50, 200) / 1000
    await page.mouse.down()
    await asyncio.sleep(hold_s)
    await page.mouse.up()


async def human_type(page: Page, text: str) -> None:
    """Type text with variable WPM, occasional typos corrected with Backspace."""
    wpm = random.uniform(HUMAN_TYPING_WPM_MIN, HUMAN_TYPING_WPM_MAX)
    char_delay_s = 60.0 / (wpm * 5)
    for char in text:
        if char.isalpha() and random.random() < HUMAN_TYPO_RATE:
            typo = random.choice("abcdefghijklmnopqrstuvwxyz")
            await page.keyboard.type(typo)
            await asyncio.sleep(max(0.02, random.gauss(char_delay_s * 0.7, char_delay_s * 0.2)))
            await page.keyboard.press("Backspace")
            await asyncio.sleep(max(0.02, random.gauss(char_delay_s * 0.5, char_delay_s * 0.1)))
        await page.keyboard.type(char)
        if random.random() < 0.05:
            await asyncio.sleep(random.uniform(0.3, 0.8))
        else:
            await asyncio.sleep(max(0.02, random.gauss(char_delay_s, char_delay_s * 0.3)))


async def human_scroll(page: Page, direction: str, amount: int) -> None:
    """Scroll in direction by amount pixels, split into variable-speed steps."""
    steps = random.randint(3, 6)
    step_amount = max(1, amount // steps)
    sign = 1 if direction == "down" else -1
    for _ in range(steps):
        delta = sign * (step_amount + random.randint(-20, 20))
        await page.mouse.wheel(0, delta)
        await asyncio.sleep(random.uniform(0.05, 0.15))
    await asyncio.sleep(random.uniform(0.5, 1.5))


async def human_pre_action_pause() -> None:
    """Short random pause simulating human reaction/thinking time."""
    await asyncio.sleep(random.uniform(0.2, 0.8))
