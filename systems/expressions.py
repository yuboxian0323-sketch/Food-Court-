"""Shared HP thresholds and frame indices for Tomato's existing expressions.

Operation:
    Centralize existing Tomato HP thresholds and normal/nervous/panic frame indices.
Input:
    Current HP and configured threshold constants.
Output:
    Expression names and shared frame indices; no mutation of HP, artwork, or motion.
"""
import settings as s

TOMATO_FRAMES = {'normal': 0, 'nervous': 2, 'panic': 3}


def tomato_expression_for_hp(hp):
    """Return the existing normal/nervous/panic expression for integer HP.

    Operation:
        Apply the existing normal/nervous HP thresholds without clamping.
    Input:
        hp and configured FACE_NORMAL_MIN_HP/FACE_NERVOUS_MIN_HP.
    Output:
        Returns normal, nervous, or panic; does not change HP or rendering state.
    """
    return ('normal' if hp >= s.FACE_NORMAL_MIN_HP else
            'nervous' if hp >= s.FACE_NERVOUS_MIN_HP else 'panic')
