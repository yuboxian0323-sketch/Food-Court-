import settings as s

TOMATO_FRAMES = {'normal': 0, 'nervous': 2, 'panic': 3}


def tomato_expression_for_hp(hp):
    
    return ('normal' if hp >= s.FACE_NORMAL_MIN_HP else
            'nervous' if hp >= s.FACE_NERVOUS_MIN_HP else 'panic')
