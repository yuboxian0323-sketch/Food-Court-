"""Round rules independent of drawing: one guarded place resolves outcomes."""
import settings as s
from entities.answer_target import make_targets, update_targets
from systems.difficulty import load_schedule, unlocked_at


class Session:
    def __init__(self, bank):
        self.bank = bank
        self.schedule = load_schedule(s.DIFFICULTY_FILE, bank.fallacies)
        s.DIFFICULTY_SCHEDULE = self.schedule
        self.restart()

    def restart(self):
        self.hp = s.START_HP
        self.score = 0
        self.counts = dict(correct=0, incorrect=0, timeout=0)
        self.number = 0
        self.unlocked = ()
        self.bank.reset()
        self.next_round()

    @property
    def game_over(self):
        return self.hp == 0

    @property
    def tint_alpha(self):
        if s.MISTAKE_TINT_DURATION <= 0:
            return 0
        return round(s.MISTAKE_TINT_ALPHA * self.tint_remaining / s.MISTAKE_TINT_DURATION)

    @property
    def objection_progress(self):
        return min(1, 1-self.animation_remaining / max(.001, s.OBJECTION_DURATION))

    def next_round(self):
        if self.game_over:
            return
        self.number += 1
        unlocked = unlocked_at(self.schedule, self.number)
        self.new_fallacies = tuple(id_ for id_ in unlocked if id_ not in self.unlocked) if self.number > 1 else ()
        self.unlocked = unlocked
        self.question = self.bank.draw(self.unlocked)
        self.choices = self.bank.choices(self.question.fallacy, self.unlocked)
        self.targets = make_targets(self.choices, self.bank.fallacies, self.bank.rng)
        self.stage = 'READING'
        self.remaining = s.ANSWER_TIME
        self.animation_remaining = self.tint_remaining = 0.0
        self.result = self.selected = None
        self.resolved = False
        self.tomato_expression = self.expression_for_hp()
        self.gadget_expression, self.chef_expression = 'talking', 'listening'

    def expression_for_hp(self):
        return ('normal' if self.hp >= s.FACE_NORMAL_MIN_HP else
                'nervous' if self.hp >= s.FACE_NERVOUS_MIN_HP else 'panic')

    def acknowledge_unlock(self):
        self.new_fallacies = ()

    def ready(self):
        if self.stage == 'READING' and not self.new_fallacies:
            self.stage = 'ANSWERING'
            self.gadget_expression, self.chef_expression = 'waiting', 'listening'

    def answer(self, choice):
        if self.stage != 'ANSWERING' or self.remaining <= 0 or choice not in self.choices:
            return False
        return self.resolve_round('correct' if choice == self.question.fallacy else 'incorrect', choice)

    def resolve_round(self, result, selected=None):
        if self.resolved or self.stage != 'ANSWERING':
            return False
        if result not in self.counts:
            raise ValueError(f'Unknown round result: {result}')
        self.resolved = True
        self.result, self.selected = result, selected
        self.counts[result] += 1
        if result == 'correct':
            self.score += s.POINTS
            self.animation_remaining = s.OBJECTION_DURATION
            self.stage = 'OBJECTION_ANIMATION'
            self.gadget_expression, self.chef_expression = 'shocked', 'surprised'
        else:
            self.hp = max(0, min(s.START_HP, self.hp - s.DAMAGE))
            self.tint_remaining = s.MISTAKE_TINT_DURATION
            self.stage = 'FEEDBACK'
            self.gadget_expression, self.chef_expression = 'smug', 'stern'
        self.tomato_expression = self.expression_for_hp()
        for target in self.targets:
            target.feedback = ('correct' if target.fallacy_id == self.question.fallacy else
                               'incorrect' if target.fallacy_id == selected else '')
        return True

    def update(self, dt):
        dt = max(0, dt)
        if self.stage == 'ANSWERING':
            active_dt = min(dt, self.remaining)
            update_targets(self.targets, active_dt)
            self.remaining = max(0.0, self.remaining - dt)
            if self.remaining == 0:
                self.resolve_round('timeout')
        elif self.stage == 'OBJECTION_ANIMATION':
            self.animation_remaining = max(0, self.animation_remaining - dt)
            if self.animation_remaining == 0:
                self.stage = 'FEEDBACK'
        elif self.stage == 'FEEDBACK':
            self.tint_remaining = max(0, self.tint_remaining - dt)
