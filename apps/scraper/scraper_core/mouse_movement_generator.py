"""Генератор реалистичных движений мыши для антидетект-функций."""

import math
import random
from typing import Dict, List, Tuple

import numpy as np


class MouseMovementGenerator:
    """Генератор реалистичных движений мыши с человеческим поведением."""

    def __init__(self):
        """Инициализация генератора."""
        self.default_params = {
            "duration_range_ms": [400, 1200],
            "steps_per_100px": 12,
            "jitter_px": 1.5,
            "overshoot_px": 8,
            "overshoot_prob": 0.15,
            "pause_prob": 0.18,
            "pause_duration_range_ms": [30, 260],
            "hover_after_ms": [80, 420],
            "easing": "easeInOutQuad",
        }

    def generate_movement(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        viewport: Tuple[int, int],
        device: str = "desktop",
        seed: int = None,
        params: Dict = None,
    ) -> Dict:
        """Генерация движения мыши."""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        final_params = {**self.default_params, **(params or {})}

        if device == "mobile":
            final_params = self._adapt_for_mobile(final_params)

        distance = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
        duration = self._calculate_duration(distance, final_params)
        step_count = self._calculate_step_count(distance, final_params)

        base_trajectory = self._generate_base_trajectory(
            start, end, step_count, final_params["easing"]
        )

        jittered_trajectory = self._add_jitter(base_trajectory, final_params["jitter_px"], distance)

        if random.random() < final_params["overshoot_prob"]:
            jittered_trajectory = self._add_overshoot(
                jittered_trajectory, final_params["overshoot_px"]
            )

        timings = self._generate_timings(
            step_count,
            duration,
            final_params["pause_prob"],
            final_params["pause_duration_range_ms"],
        )

        steps = self._create_steps(jittered_trajectory, timings)

        if random.random() < 0.3:
            hover_duration = random.randint(
                final_params["hover_after_ms"][0], final_params["hover_after_ms"][1]
            )
            steps.append({"x": end[0], "y": end[1], "t": steps[-1]["t"] + hover_duration})

        return {
            "steps": steps,
            "meta": {
                "total_duration_ms": steps[-1]["t"] if steps else 0,
                "step_count": len(steps),
                "used_params": final_params,
                "distance_px": distance,
                "device": device,
            },
        }

    def _adapt_for_mobile(self, params: Dict) -> Dict:
        """Адаптация параметров для мобильных устройств."""
        mobile_params = params.copy()
        mobile_params["steps_per_100px"] = max(8, params["steps_per_100px"] - 4)
        mobile_params["jitter_px"] = params["jitter_px"] * 0.8
        mobile_params["overshoot_px"] = params["overshoot_px"] * 0.6
        mobile_params["overshoot_prob"] = params["overshoot_prob"] * 0.7
        mobile_params["pause_prob"] = params["pause_prob"] * 1.2
        return mobile_params

    def _calculate_duration(self, distance: float, params: Dict) -> int:
        """Вычисление длительности движения."""
        min_duration, max_duration = params["duration_range_ms"]
        base_duration = random.randint(min_duration, max_duration)
        distance_factor = min(1.5, distance / 500)
        return int(base_duration * (1 + distance_factor * 0.3))

    def _calculate_step_count(self, distance: float, params: Dict) -> int:
        """Вычисление количества шагов."""
        steps_per_100px = params["steps_per_100px"]
        base_steps = max(20, int(distance / 100 * steps_per_100px))
        variation = random.randint(-5, 10)
        return min(120, max(20, base_steps + variation))

    def _generate_base_trajectory(
        self, start: Tuple[int, int], end: Tuple[int, int], step_count: int, easing: str
    ) -> List[Tuple[float, float]]:
        """Генерация базовой траектории."""
        trajectory = []

        for i in range(step_count):
            t = i / (step_count - 1) if step_count > 1 else 0
            eased_t = self._apply_easing(t, easing)

            x = start[0] + (end[0] - start[0]) * eased_t
            y = start[1] + (end[1] - start[1]) * eased_t

            trajectory.append((x, y))

        return trajectory

    def _apply_easing(self, t: float, easing: str) -> float:
        """Применение easing функции."""
        if easing == "easeInOutQuad":
            if t < 0.5:
                return 2 * t * t
            else:
                return -1 + (4 - 2 * t) * t
        elif easing == "easeInOutCubic":
            if t < 0.5:
                return 4 * t * t * t
            else:
                return (t - 1) * (2 * t - 2) * (2 * t - 2) + 1
        else:
            return t

    def _add_jitter(
        self, trajectory: List[Tuple[float, float]], jitter_px: float, distance: float
    ) -> List[Tuple[float, float]]:
        """Добавление случайных отклонений."""
        jittered = []

        for i, (x, y) in enumerate(trajectory):
            progress = i / (len(trajectory) - 1) if len(trajectory) > 1 else 0
            current_jitter = jitter_px * (1 - progress * 0.7)

            jitter_x = np.random.normal(0, current_jitter)
            jitter_y = np.random.normal(0, current_jitter)

            jittered.append((x + jitter_x, y + jitter_y))

        return jittered

    def _add_overshoot(
        self, trajectory: List[Tuple[float, float]], overshoot_px: float
    ) -> List[Tuple[float, float]]:
        """Добавление overshoot."""
        if len(trajectory) < 3:
            return trajectory

        overshoot_index = int(len(trajectory) * random.uniform(0.8, 0.9))

        if overshoot_index > 0:
            dx = trajectory[overshoot_index][0] - trajectory[overshoot_index - 1][0]
            dy = trajectory[overshoot_index][1] - trajectory[overshoot_index - 1][1]
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                dx /= length
                dy /= length

                overshoot_x = trajectory[overshoot_index][0] + dx * overshoot_px
                overshoot_y = trajectory[overshoot_index][1] + dy * overshoot_px

                trajectory.insert(overshoot_index + 1, (overshoot_x, overshoot_y))

        return trajectory

    def _generate_timings(
        self, step_count: int, duration: int, pause_prob: float, pause_duration_range: List[int]
    ) -> List[int]:
        """Генерация таймингов."""
        timings = []
        current_time = 0

        for i in range(step_count):
            timings.append(current_time)

            base_delay = duration / step_count

            if random.random() < pause_prob:
                pause_duration = random.randint(pause_duration_range[0], pause_duration_range[1])
                current_time += base_delay + pause_duration
            else:
                variation = random.uniform(0.8, 1.2)
                current_time += base_delay * variation

        return timings

    def _create_steps(
        self, trajectory: List[Tuple[float, float]], timings: List[int]
    ) -> List[Dict]:
        """Создание финальных шагов движения."""
        steps = []

        for i, ((x, y), t) in enumerate(zip(trajectory, timings)):
            steps.append({"x": int(round(x)), "y": int(round(y)), "t": int(round(t))})

        return steps


def generate_mouse_movement(
    start: Tuple[int, int],
    end: Tuple[int, int],
    viewport: Tuple[int, int] = (1920, 1080),
    device: str = "desktop",
    seed: int = None,
    params: Dict = None,
) -> Dict:
    """Быстрая генерация движения мыши."""
    generator = MouseMovementGenerator()
    return generator.generate_movement(start, end, viewport, device, seed, params)
