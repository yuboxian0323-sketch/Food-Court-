"""Exercise explicit board/result transitions in gameplay checks."""
import settings as s


def begin_answering(session):
    session.ready()
    session.update(s.BOARD_ENTER_DURATION)


def finish_result(session):
    session.update(session.animation_remaining)


def ready_frame(game,click):
    game.frame([click],0)
    game.frame([],s.BOARD_ENTER_DURATION)
