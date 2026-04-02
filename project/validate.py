#!/usr/bin/env python
"""Validation script for the Smart Waste Management Environment."""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_imports() -> bool:
    logger.info("Testing imports...")
    try:
        from env.environment import SmartWasteManagementEnvironment
        from env.grader import PerformanceGrader
        from env.models import Action, EnvironmentState, GarbageTruck, WasteBin
        from env.tasks import TaskRegistry

        _ = (WasteBin, GarbageTruck, EnvironmentState, Action, SmartWasteManagementEnvironment, TaskRegistry, PerformanceGrader)
        logger.info("[OK] All imports successful")
        return True
    except Exception as exc:
        logger.error("[FAIL] Import failed: %s", exc)
        return False


def test_environment_creation() -> bool:
    logger.info("Testing environment creation...")
    try:
        from env.environment import SmartWasteManagementEnvironment
        from env.tasks import TaskRegistry

        env = SmartWasteManagementEnvironment(TaskRegistry.get_task("easy"))
        state = env.reset()

        assert state is not None
        assert len(state.bins) == 5
        assert state.truck.current_load == 0.0
        assert state.time_step == 0

        logger.info("[OK] Environment creation successful")
        return True
    except Exception as exc:
        logger.error("[FAIL] Environment creation failed: %s", exc)
        return False


def test_environment_step() -> bool:
    logger.info("Testing environment steps...")
    try:
        from env.environment import SmartWasteManagementEnvironment
        from env.models import Action
        from env.tasks import TaskRegistry

        env = SmartWasteManagementEnvironment(TaskRegistry.get_task("easy"))
        env.reset()

        wait_result = env.step(Action(action_type="wait"))
        assert wait_result.state is not None
        assert wait_result.done is False

        move_result = env.step(Action(action_type="move", target_location=1))
        assert move_result.state.truck.location == 1

        logger.info("[OK] Environment steps successful")
        return True
    except Exception as exc:
        logger.error("[FAIL] Environment steps failed: %s", exc)
        return False


def test_grading() -> bool:
    logger.info("Testing grading system...")
    try:
        from env.environment import SmartWasteManagementEnvironment
        from env.grader import PerformanceGrader
        from env.models import Action
        from env.tasks import TaskRegistry

        env = SmartWasteManagementEnvironment(TaskRegistry.get_task("easy"))
        initial_state = env.reset()
        total_reward = 0.0

        for _ in range(10):
            total_reward += env.step(Action(action_type="wait")).reward

        score = PerformanceGrader.grade_episode(initial_state, env.state(), total_reward)
        assert 0.0 <= score <= 1.0

        logger.info("[OK] Grading system successful (score: %.3f)", score)
        return True
    except Exception as exc:
        logger.error("[FAIL] Grading system failed: %s", exc)
        return False


def test_fastapi() -> bool:
    logger.info("Testing FastAPI setup...")
    try:
        import fastapi
        import pydantic
        import uvicorn

        _ = (fastapi, pydantic, uvicorn)
        logger.info("[OK] FastAPI dependencies available")
        return True
    except Exception as exc:
        logger.error("[FAIL] FastAPI dependencies missing: %s", exc)
        return False


def test_all_tasks() -> bool:
    logger.info("Testing all task levels...")
    try:
        from env.environment import SmartWasteManagementEnvironment
        from env.tasks import TaskRegistry

        for task_name in ["easy", "medium", "hard"]:
            task = TaskRegistry.get_task(task_name)
            state = SmartWasteManagementEnvironment(task).reset()
            assert len(state.bins) == task.num_bins
            assert state.truck.max_capacity == task.truck_capacity
            logger.info("  [OK] %s: %s bins, %s steps", task_name, task.num_bins, task.time_limit)

        return True
    except Exception as exc:
        logger.error("[FAIL] Task testing failed: %s", exc)
        return False


def main() -> int:
    print("=" * 60)
    print("Smart Waste Management Environment - Validation")
    print("=" * 60)
    print()

    tests = [
        test_imports,
        test_environment_creation,
        test_environment_step,
        test_grading,
        test_fastapi,
        test_all_tasks,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as exc:
            logger.error("[FAIL] Test %s crashed: %s", test.__name__, exc)
            results.append(False)
        print()

    passed = sum(results)
    total = len(results)
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("[OK] All validations PASSED - Ready to use!")
        print("=" * 60)
        return 0

    print("[FAIL] Some validations FAILED - Check errors above")
    print("=" * 60)
    return 1


if __name__ == "__main__":
    sys.exit(main())
