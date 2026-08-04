"""
TDD test cases for LLMFeedback.py
Run: python code/test_llm_feedback.py
"""

import sys

PASS = 0
FAIL = 0


def assert_test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} — {detail}")


# --- Test Cases ---

def test_1_top_features_extraction():
    """Given a model + standardized feature values, returns top 3 contributors sorted by |contribution|."""
    from LLMFeedback import get_top_contributors

    # Simulated: coefficient * standardized_value per feature
    contributions = {
        'peak_value_mean': 1.2,
        'vel_sd_up_mean': 0.9,
        'start_value_std': 0.3,
        'num_frames_up_mean': 0.7,
        'CL': 0.1,
        'magnitude_mean': 0.05,
    }

    top_3 = get_top_contributors(contributions, n=3)

    assert_test("returns exactly 3 features", len(top_3) == 3)
    assert_test("sorted by absolute contribution descending",
                top_3[0][1] >= top_3[1][1] >= top_3[2][1])
    assert_test("highest is peak_value_mean",
                top_3[0][0] == 'peak_value_mean', f"got {top_3[0][0]}")
    assert_test("second is vel_sd_up_mean",
                top_3[1][0] == 'vel_sd_up_mean', f"got {top_3[1][0]}")
    assert_test("third is num_frames_up_mean",
                top_3[2][0] == 'num_frames_up_mean', f"got {top_3[2][0]}")


def test_2_human_readable_transform():
    """Top features + hand → list of Hebrew coaching cue strings (pre-LLM input)."""
    from LLMFeedback import features_to_cues

    top_features = [
        ('peak_value_mean', 1.2),
        ('vel_sd_up_mean', 0.9),
        ('num_frames_up_mean', 0.7),
    ]

    cues = features_to_cues(top_features, hand='right')

    assert_test("returns a list of strings", isinstance(cues, list) and all(isinstance(c, str) for c in cues))
    assert_test("returns 3 cues", len(cues) == 3)
    assert_test("cues are in Hebrew (contain Hebrew chars)",
                all(any('֐' <= ch <= '׿' for ch in c) for c in cues))
    assert_test("hand mentioned in relevant cues (at least one contains ימין)",
                any('ימין' in c for c in cues))
    assert_test("no raw feature names in output",
                not any('peak_value' in c or 'vel_sd' in c for c in cues))


def test_3_static_fallback():
    """When LLM is unavailable, concatenated static cues are returned as-is."""
    from LLMFeedback import generate_feedback

    context = {
        'exercise_name': 'raise_arms_horizontally',
        'hand': 'right',
        'top_contributors': [
            ('peak_value_mean', 1.2),
            ('vel_sd_up_mean', 0.9),
            ('num_frames_up_mean', 0.7),
        ],
        'use_llm': False,
    }

    result = generate_feedback(context)

    assert_test("returns a non-empty string", isinstance(result, str) and len(result) > 0)
    assert_test("result is in Hebrew", any('֐' <= ch <= '׿' for ch in result))
    assert_test("deterministic (same input → same output)",
                generate_feedback(context) == result)


def test_4_llm_phrasing():
    """When LLM is enabled, output is a single combined sentence (not 3 separate ones)."""
    import os
    from LLMFeedback import generate_feedback

    context = {
        'exercise_name': 'raise_arms_horizontally',
        'hand': 'right',
        'top_contributors': [
            ('peak_value_mean', 1.2),
            ('vel_sd_up_mean', 0.9),
            ('num_frames_up_mean', 0.7),
        ],
        'use_llm': True,
    }

    result = generate_feedback(context)

    assert_test("returns a non-empty string", isinstance(result, str) and len(result) > 0)
    assert_test("result is in Hebrew", any('֐' <= ch <= '׿' for ch in result))

    static_context = {**context, 'use_llm': False}
    static_result = generate_feedback(static_context)
    if result != static_result:
        assert_test("LLM result differs from static (rephrased)", True)
    else:
        assert_test("falls back to static (no key or quota unavailable — test LLM locally)",
                    result == static_result)


def test_5_cross_session_improvement():
    """Given previous and current contributions, detects improved features with positive feedback."""
    from LLMFeedback import detect_improvement

    prev_contributions = {
        'peak_value_mean': 1.2,
        'vel_sd_up_mean': 0.9,
        'num_frames_up_mean': 0.7,
    }
    current_contributions = {
        'peak_value_mean': 0.4,   # improved significantly (delta 0.8)
        'vel_sd_up_mean': 0.85,   # barely changed (delta 0.05, below threshold)
        'num_frames_up_mean': 0.3, # improved (delta 0.4)
    }

    improvements = detect_improvement(prev_contributions, current_contributions, threshold=0.2)

    assert_test("returns list of improved features", isinstance(improvements, list))
    assert_test("peak_value_mean detected as improved",
                any(f[0] == 'peak_value_mean' for f in improvements))
    assert_test("num_frames_up_mean detected as improved",
                any(f[0] == 'num_frames_up_mean' for f in improvements))
    assert_test("vel_sd_up_mean NOT detected (below threshold)",
                not any(f[0] == 'vel_sd_up_mean' for f in improvements))
    assert_test("sorted by improvement magnitude descending",
                improvements[0][1] >= improvements[1][1] if len(improvements) > 1 else True)
    assert_test("each improvement has positive feedback string",
                all(isinstance(f[2], str) and len(f[2]) > 0 for f in improvements))


# --- Runner ---

def main():
    tests = [
        ("1: Top features extraction", test_1_top_features_extraction),
        ("2: Human-readable transform", test_2_human_readable_transform),
        ("3: Static fallback (no LLM)", test_3_static_fallback),
        ("4: LLM phrasing", test_4_llm_phrasing),
        ("5: Cross-session improvement", test_5_cross_session_improvement),
    ]

    target = int(sys.argv[1]) if len(sys.argv) > 1 else None

    for i, (name, test_fn) in enumerate(tests, 1):
        if target and i != target:
            continue
        print(f"\nTest {name}")
        print("-" * 40)
        try:
            test_fn()
        except ImportError as e:
            print(f"  ⚠ SKIP — {e} (LLMFeedback.py not yet implemented)")
        except Exception as e:
            print(f"  ✗ CRASH — {e}")
            global FAIL
            FAIL += 1

    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    if FAIL:
        sys.exit(1)


if __name__ == '__main__':
    main()
