"""
LLM-powered feedback module for adaptive exercise training.
Uses feature importance (coefficient × standardized value) to generate
targeted, positive Hebrew coaching cues via Gemini Flash.

Static map is the core mechanism; LLM is an optional phrasing layer.
"""

import os
from pathlib import Path

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Load .env file from same directory as this script
_env_path = Path(__file__).parent / '.env'
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            os.environ.setdefault(key.strip(), val.strip())

# --- Feature-to-Hebrew cue mapping (positive tone) ---

HAND_NAMES = {'right': 'ימין', 'left': 'שמאל'}

FEATURE_CUES = {
    'peak_value_mean': "נסה להגיע לטווח תנועה מלא עם יד {hand}",
    'peak_value_std': "נסה להגיע לאותו גובה בכל חזרה",
    'start_value_mean': "נסה להתחיל כל חזרה מאותה נקודה",
    'start_value_std': "נסה לשמור על עקביות בנקודת ההתחלה",
    'end_value_mean': "נסה לחזור לאותה נקודה בסוף כל חזרה",
    'end_value_std': "נסה לסיים כל חזרה באותו מקום",
    'num_frames_up_mean': "נסה להאיץ קצת את התנועה למעלה",
    'num_frames_up_std': "נסה לשמור על קצב אחיד בין חזרות",
    'num_frames_down_mean': "נסה להוריד בקצב שווה",
    'num_frames_down_std': "נסה לשמור על אותו קצב ירידה בכל חזרה",
    'vel_mean_up_mean': "נסה להגביר קצת את המהירות בדרך למעלה",
    'vel_mean_up_std': "נסה לשמור על מהירות עקבית בעלייה",
    'vel_sd_up_mean': "נסה לנוע בצורה חלקה יותר בדרך למעלה",
    'vel_sd_up_std': "נסה לשמור על חלקות עקבית בעלייה",
    'acc_mean_up_mean': "נסה לבנות תאוצה חלקה בדרך למעלה",
    'acc_mean_up_std': "נסה לשמור על תאוצה עקבית בעלייה",
    'acc_sd_up_mean': "נסה לשמור על תנועה יציבה בדרך למעלה",
    'acc_sd_up_std': "נסה להיות עקבי ביציבות התנועה למעלה",
    'vel_mean_down_mean': "נסה לשלוט יותר בירידה — לאט יותר",
    'vel_mean_down_std': "נסה לשמור על מהירות ירידה עקבית",
    'vel_sd_down_mean': "נסה להוריד את הידיים בצורה חלקה יותר",
    'vel_sd_down_std': "נסה לשמור על חלקות עקבית בירידה",
    'acc_mean_down_mean': "נסה לשלוט בתאוצה בדרך למטה",
    'acc_mean_down_std': "נסה לשמור על ירידה עקבית",
    'acc_sd_down_mean': "נסה לשמור על תנועה יציבה בירידה",
    'acc_sd_down_std': "נסה להיות עקבי ביציבות הירידה",
    'freq_num': "נסה לפשט את התנועה — פחות תנועות מיותרות",
    'magnitude_mean': "נסה לשמור על קצב תנועה יציב יותר",
    'magnitude_sd': "נסה לשמור על עקביות בקצב התנועה",
    'DF1_freq': "נסה לשמור על קצב קבוע",
    'DF1_mag': "נסה לחזק את הקצב הבסיסי של התנועה",
    'DF2_freq': "נסה למזער תנועות משניות",
    'DF2_mag': "נסה להתמקד בתנועה הראשית",
    'DF3_freq': "נסה למזער רעשי תנועה",
    'DF3_mag': "נסה לשמור על תנועה נקייה",
    'CL': "נסה לקצר את החזרות — לשמור על מומנטום",
    'cycles_num': "נסה להשלים את כל החזרות",
    'rep': "נסה להשלים את כל סט החזרות",
}

IMPROVEMENT_CUES = {
    'peak_value_mean': "טווח התנועה שלך השתפר מהפעם הקודמת עם יד {hand}!",
    'peak_value_std': "העקביות בגובה שלך השתפרה!",
    'start_value_mean': "נקודת ההתחלה שלך יותר מדויקת!",
    'start_value_std': "ההתחלות שלך יותר עקביות — כל הכבוד!",
    'vel_sd_up_mean': "התנועה שלך חלקה יותר מהפעם הקודמת!",
    'vel_sd_down_mean': "הירידה שלך חלקה יותר — יפה!",
    'num_frames_up_mean': "הקצב שלך השתפר!",
    'num_frames_up_std': "הקצב שלך יציב יותר — כל הכבוד!",
    'CL': "אורך החזרות שלך השתפר!",
    'acc_sd_up_mean': "התנועה שלך יציבה יותר — מעולה!",
    'acc_sd_down_mean': "השליטה בירידה השתפרה!",
}


# --- Core functions ---

def get_top_contributors(contributions: dict, n=3) -> list:
    """Return top N features sorted by absolute contribution (descending)."""
    sorted_features = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
    return sorted_features[:n]


def features_to_cues(top_features: list, hand: str) -> list:
    """Transform feature names + hand → list of Hebrew coaching cue strings."""
    hand_heb = HAND_NAMES.get(hand, hand or '')
    cues = []
    for feature_name, _ in top_features:
        template = FEATURE_CUES.get(feature_name, "נסה לשפר את הביצוע עם יד {hand}")
        cues.append(template.format(hand=hand_heb))
    return cues


def generate_feedback(context: dict) -> str:
    """
    Generate Hebrew coaching feedback.

    context keys:
        exercise_name: str
        hand: str ('right'|'left'|'')
        top_contributors: list of (feature_name, contribution_value)
        use_llm: bool
    """
    top_features = context['top_contributors']
    hand = context.get('hand', '')
    cues = features_to_cues(top_features, hand)
    static_result = ' '.join(cues)

    if not context.get('use_llm', False):
        return static_result

    # LLM rephrasing via Gemini Flash
    if not GEMINI_AVAILABLE:
        return static_result

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return static_result

    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            "אתה מאמן כושר מעודד. שלב את 3 ההנחיות הבאות למשפט אחד טבעי ומעודד בעברית. "
            "שמור על טון חיובי. אל תוסיף מידע שלא נמצא בהנחיות. "
            "החזר רק את המשפט, בלי הסברים.\n\n"
            f"הנחיות:\n" + "\n".join(f"- {c}" for c in cues)
        )
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        result = response.text.strip()
        if result:
            return result
    except Exception:
        pass

    return static_result


def detect_improvement(prev_contributions: dict, current_contributions: dict,
                       threshold=0.2) -> list:
    """
    Compare contributions across sessions.
    Returns list of (feature_name, delta, improvement_cue) for improved features.
    Positive delta = improvement (prev was worse).
    """
    improvements = []
    for feature, prev_val in prev_contributions.items():
        curr_val = current_contributions.get(feature)
        if curr_val is None:
            continue
        delta = prev_val - curr_val
        if delta > threshold:
            template = IMPROVEMENT_CUES.get(feature, "הביצוע שלך השתפר ב{feature}!")
            cue = template.format(hand=HAND_NAMES.get('right', ''), feature=feature)
            improvements.append((feature, delta, cue))

    improvements.sort(key=lambda x: x[1], reverse=True)
    return improvements
