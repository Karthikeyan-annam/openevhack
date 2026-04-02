import json
import logging
import os
from typing import Dict, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from env.environment import SmartWasteManagementEnvironment
from env.grader import PerformanceGrader
from env.models import Action
from env.tasks import TaskRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class EnvironmentAgent:
    """LLM-backed agent with a strong deterministic fallback policy."""

    def __init__(self):
        self.api_base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
        self.model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        self.hf_token = os.getenv("HF_TOKEN", "").strip()
        self.client = None

        if OpenAI is None:
            logger.warning("OpenAI client not installed. Using heuristic agent.")
        elif not self.hf_token:
            logger.warning("HF_TOKEN not set. Using heuristic agent.")
        else:
            self.client = OpenAI(api_key=self.hf_token, base_url=self.api_base_url)

        logger.info(
            "Agent initialized: model=%s, base_url=%s",
            self.model_name,
            self.api_base_url,
        )

    def decide_action(self, observation: Dict[str, object], available_bins: int) -> Action:
        if self.client is not None:
            try:
                return self._llm_decision(observation, available_bins)
            except Exception as exc:
                logger.warning("LLM failed (%s), falling back to heuristic agent.", exc)
        return self._heuristic_decision(observation)

    def _llm_decision(self, observation: Dict[str, object], available_bins: int) -> Action:
        prompt = self._format_prompt(observation, available_bins)
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You optimize municipal waste collection. "
                        "Return only compact JSON with action_type, bin_id, and target_location."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=120,
        )

        content = (response.choices[0].message.content or "").strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        action_data = json.loads(content)
        return Action(
            action_type=action_data.get("action_type", "wait"),
            bin_id=action_data.get("bin_id", -1),
            target_location=action_data.get("target_location", -1),
        )

    def _heuristic_decision(self, observation: Dict[str, object]) -> Action:
        bin_levels = observation["bin_levels"]
        bin_locations = observation["bin_locations"]
        truck_location = observation["truck_location"]
        current_load = observation["current_load"]
        truck_capacity = observation["truck_capacity"]

        remaining_capacity = truck_capacity - current_load
        bins_here = [
            (index, level)
            for index, (level, location) in enumerate(zip(bin_levels, bin_locations))
            if location == truck_location and level > 0.0
        ]
        bins_here.sort(key=lambda item: item[1], reverse=True)

        urgent_bins = sorted(
            [
                (index, level, location)
                for index, (level, location) in enumerate(zip(bin_levels, bin_locations))
                if level >= 85.0
            ],
            key=lambda item: item[1],
            reverse=True,
        )

        if bins_here and remaining_capacity > 0.0:
            top_bin_id, top_level = bins_here[0]
            if top_level >= 35.0 or any(level >= 85.0 for _, level in bins_here):
                return Action(action_type="collect", bin_id=top_bin_id)

        if remaining_capacity <= truck_capacity * 0.1 and truck_location != 0:
            return Action(action_type="move", target_location=0)

        if urgent_bins:
            urgent_location = urgent_bins[0][2]
            if urgent_location != truck_location:
                return Action(action_type="move", target_location=urgent_location)

        location_pressure: Dict[int, float] = {}
        for level, location in zip(bin_levels, bin_locations):
            location_pressure[location] = location_pressure.get(location, 0.0) + level

        best_location = max(location_pressure, key=location_pressure.get)
        if best_location != truck_location:
            return Action(action_type="move", target_location=best_location)

        if bins_here and remaining_capacity > 0.0:
            return Action(action_type="collect", bin_id=bins_here[0][0])

        return Action(action_type="wait")

    def _format_prompt(self, observation: Dict[str, object], available_bins: int) -> str:
        return (
            "Current environment state:\n"
            f"- Bin fill levels: {observation['bin_levels']}\n"
            f"- Bin locations: {observation['bin_locations']}\n"
            f"- Truck load: {observation['current_load']} / {observation['truck_capacity']}\n"
            f"- Truck location: {observation['truck_location']}\n"
            f"- Truck fuel: {observation['truck_fuel']}\n"
            f"- Time step: {observation['time']} of {observation['time_limit']}\n"
            f"- Total collected: {observation['total_collected']}\n"
            f"- Total overflows: {observation['total_overflows']}\n\n"
            "Valid actions:\n"
            f"1. collect a bin id from 0 to {available_bins - 1}\n"
            "2. move to a location from 0 to 4\n"
            "3. wait\n\n"
            "Respond as JSON like "
            '{"action_type":"collect","bin_id":2,"target_location":-1}'
        )


def run_episode(
    env: SmartWasteManagementEnvironment,
    agent: EnvironmentAgent,
    max_steps: Optional[int] = None,
) -> Dict[str, object]:
    initial_state = env.reset()
    total_reward = 0.0
    step_count = 0

    while True:
        observation = env.get_observation_dict()
        action = agent.decide_action(observation, len(initial_state.bins))
        result = env.step(action)
        total_reward += result.reward
        step_count += 1

        if result.done or (max_steps is not None and step_count >= max_steps):
            break

    final_state = env.state()
    return {
        "initial_state": initial_state,
        "final_state": final_state,
        "total_reward": total_reward,
        "steps": step_count,
        "total_collected": final_state.total_collected,
        "total_overflows": final_state.total_overflows,
    }


def main() -> Dict[str, Dict[str, object]]:
    print("Running Smart Waste Management Environment...\n")

    agent = EnvironmentAgent()
    results: Dict[str, Dict[str, object]] = {}

    for task_name in TaskRegistry.list_tasks():
        task = TaskRegistry.get_task(task_name)
        env = SmartWasteManagementEnvironment(task)
        episodes = [run_episode(env, agent) for _ in range(3)]
        grades = PerformanceGrader.grade_batch(episodes)
        results[task_name] = {"episodes": episodes, "grades": grades}
        print(f"Task: {task_name} -> Score: {grades['avg_score']:.2f}")

    final_average = sum(item["grades"]["avg_score"] for item in results.values()) / len(results)
    print(f"\nFinal Average Score: {final_average:.2f}")
    return results


if __name__ == "__main__":
    main()
