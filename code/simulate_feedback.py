"""
Simulate the feedback trigger point for LLM development.
Sets up all state that would exist when corrective/adaptation feedback fires,
without requiring camera, robot, MediaPipe, or CoppeliaSim.

Usage:
    python code/simulate_feedback.py        # run all scenarios
    python code/simulate_feedback.py 3      # run scenario 3 only
"""

import sys
from dataclasses import dataclass

import Settings as s

s.__init__()


# --- Angle thresholds from Camera.py ---

EXERCISE_THRESHOLDS = {
    'raise_arms_horizontally': {'up': (80, 105), 'down': (5, 30)},
    'bend_elbows': {'up': (150, 180), 'down': (10, 50)},
    'raise_arms_bend_elbows': {'up': (130, 180), 'down': (10, 70)},
    'open_and_close_arms': {'up': (90, 120), 'down': (150, 175)},
    'open_and_close_arms_90': {'up': (140, 180), 'down': (80, 120)},
    'raise_arms_forward': {'up': (85, 135), 'down': (10, 50)},
}


# --- LLM feedback interface (stub) ---

def generate_feedback(context: dict) -> str:
    """
    Stub for the LLM feedback module.
    Input: context dict with performance signals.
    Output: Hebrew coaching cue string.

    Replace this with a real LLM call when LLMFeedback.py is built.
    """
    # ponytail: stub returns canned Hebrew; swap for LLM call later
    if context['feedback_type'] == 'corrective':
        if context['flag']:
            return f"[LLM stub] נסה להרים את הידיים יותר גבוה — {context['exercise_name']}"
        else:
            return f"[LLM stub] נסה לסגור את הידיים יותר — {context['exercise_name']}"
    elif context['feedback_type'] == 'adaptation_decision':
        return f"[LLM stub] סיימנו הערכה — עכשיו נתאמן על {context['one_hand'] or 'שתי הידיים'}"
    else:
        return "[LLM stub] כל הכבוד! בוא ננסה שוב"


# --- Scenarios ---

@dataclass
class Scenario:
    name: str
    description: str
    context: dict


def build_scenarios() -> list:
    exercise = 'raise_arms_horizontally'
    thresholds = EXERCISE_THRESHOLDS[exercise]

    return [
        Scenario(
            name="Both hands problematic (flag=True → raise more)",
            description="Corrective feedback fires mid-exercise, user needs to raise higher",
            context={
                'exercise_name': exercise,
                'performance_class': {exercise: {'right': 1.5, 'left': 0.8}},
                'counter': 1,
                'robot_rep': 4,
                'rep': 8,
                'one_hand': False,
                'flag': True,
                'current_angle': 55.0,
                'target_range': thresholds['up'],
                'feedback_type': 'corrective',
            },
        ),
        Scenario(
            name="Both hands problematic (flag=False → close more)",
            description="Corrective feedback fires mid-exercise, user needs to close more",
            context={
                'exercise_name': exercise,
                'performance_class': {exercise: {'right': 1.2, 'left': 1.0}},
                'counter': 2,
                'robot_rep': 5,
                'rep': 8,
                'one_hand': False,
                'flag': False,
                'current_angle': 45.0,
                'target_range': thresholds['down'],
                'feedback_type': 'corrective',
            },
        ),
        Scenario(
            name="Right hand only problematic",
            description="Adaptation decided right hand needs focused training",
            context={
                'exercise_name': exercise + '_one_hand',
                'performance_class': {exercise: {'right': 1.8, 'left': 0.3}},
                'counter': 1,
                'robot_rep': 4,
                'rep': 8,
                'one_hand': 'right',
                'flag': True,
                'current_angle': 60.0,
                'target_range': thresholds['up'],
                'feedback_type': 'corrective',
            },
        ),
        Scenario(
            name="Left hand only problematic",
            description="Adaptation decided left hand needs focused training",
            context={
                'exercise_name': exercise + '_one_hand',
                'performance_class': {exercise: {'right': 0.2, 'left': 1.6}},
                'counter': 0,
                'robot_rep': 5,
                'rep': 8,
                'one_hand': 'left',
                'flag': True,
                'current_angle': 50.0,
                'target_range': thresholds['up'],
                'feedback_type': 'corrective',
            },
        ),
        Scenario(
            name="No problems (encouragement)",
            description="Both hands performed well — encourage and let user lead",
            context={
                'exercise_name': exercise,
                'performance_class': {exercise: {'right': 0.4, 'left': 0.5}},
                'counter': 7,
                'robot_rep': 8,
                'rep': 8,
                'one_hand': False,
                'flag': True,
                'current_angle': 92.0,
                'target_range': thresholds['up'],
                'feedback_type': 'encouragement',
            },
        ),
        Scenario(
            name="Adaptation decision moment",
            description="Assessment complete, about to announce adaptation result",
            context={
                'exercise_name': exercise,
                'performance_class': {
                    'raise_arms_horizontally': {'right': 1.3, 'left': 0.9},
                    'bend_elbows': {'right': 1.1, 'left': 0.7},
                },
                'counter': 6,
                'robot_rep': 8,
                'rep': 8,
                'one_hand': False,
                'flag': True,
                'current_angle': 90.0,
                'target_range': thresholds['up'],
                'feedback_type': 'adaptation_decision',
            },
        ),
    ]


def populate_settings(ctx: dict):
    """Set Settings globals to match scenario state."""
    s.performance_class = ctx['performance_class']
    s.corrective_feedback = ctx['feedback_type'] == 'corrective'
    s.one_hand = ctx['one_hand']
    s.robot_rep = ctx['robot_rep']
    s.rep = ctx['rep']
    s.adaptive = True


def run_scenario(scenario: Scenario, index: int):
    print(f"\n{'='*60}")
    print(f"  Scenario {index}: {scenario.name}")
    print(f"  {scenario.description}")
    print(f"{'='*60}")

    populate_settings(scenario.context)

    print(f"\n  State:")
    print(f"    exercise:    {scenario.context['exercise_name']}")
    print(f"    perf_class:  {scenario.context['performance_class']}")
    print(f"    counter:     {scenario.context['counter']} / robot_rep: {scenario.context['robot_rep']}")
    print(f"    one_hand:    {scenario.context['one_hand']}")
    print(f"    flag:        {scenario.context['flag']}")
    print(f"    angle:       {scenario.context['current_angle']}° (target: {scenario.context['target_range']})")
    print(f"    type:        {scenario.context['feedback_type']}")

    # Verify trigger condition would fire (for corrective scenarios)
    if scenario.context['feedback_type'] == 'corrective':
        triggers = (
            s.corrective_feedback
            and s.robot_rep >= s.rep / 2
            and scenario.context['counter'] <= 2
        )
        print(f"    trigger:     {'FIRES ✓' if triggers else 'would NOT fire ✗'}")

    feedback = generate_feedback(scenario.context)
    print(f"\n  LLM output: {feedback}")


def main():
    scenarios = build_scenarios()

    if len(sys.argv) > 1:
        idx = int(sys.argv[1])
        if 1 <= idx <= len(scenarios):
            run_scenario(scenarios[idx - 1], idx)
        else:
            print(f"Error: scenario must be 1-{len(scenarios)}, got {idx}")
            sys.exit(1)
    else:
        for i, scenario in enumerate(scenarios, 1):
            run_scenario(scenario, i)

    print(f"\n{'='*60}")
    print("  Done. Replace generate_feedback() with LLM call next.")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
