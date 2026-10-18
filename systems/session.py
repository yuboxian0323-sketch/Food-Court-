"""Round rules independent of drawing: one guarded place resolves outcomes.

Operation:
    Own round progression, stage clocks, and guarded outcome application.
Input:
    Validated content bank, difficulty schedule, gameplay settings, answers, and elapsed
    seconds.
Output:
    Session totals, questions/targets, expressions, and stages; no save files are
    produced.
"""
import settings as s
from entities.answer_target import make_targets, update_targets
from systems.difficulty import load_schedule, unlocked_at
from systems.expressions import tomato_expression_for_hp


class Session:
    """Own round state and guard all scoring, damage, and outcome transitions.

    Operation:
        Own round state and guard exactly-once score, damage, and transitions.
    Input:
        Validated bank, difficulty schedule, settings, and event/update calls.
    Output:
        Mutable session totals, current question/targets, stage clocks, and reactions.
    """

    def __init__(self, bank):
        """Validate the bank unlock schedule, publish it to settings, and restart.

        Operation:
            Validate/publish the difficulty schedule, then initialize a new session.
        Input:
            bank and DIFFICULTY_FILE.
        Output:
            Sets schedule/settings schedule and restarts; schedule ContentError
            propagates.
        """
        self.bank = bank
        self.schedule = load_schedule(s.DIFFICULTY_FILE, bank.fallacies)
        s.DIFFICULTY_SCHEDULE = self.schedule
        self.restart()

    def restart(self):
        """Clear session totals and unlock history, then prepare the first round.

        Operation:
            Clear totals/unlocks and reset the content bag before preparing round one.
        Input:
            Current Session and QuestionBank; configured starting HP.
        Output:
            Resets round/session/animation state without reseeding RNG; returns None.
        """
        self.hp = s.START_HP
        self.score = 0
        self.counts = dict(correct=0, incorrect=0, timeout=0)
        self.number = 0
        self.unlocked = ()
        self.bank.reset()
        self.next_round()

    @property
    def game_over(self):
        """Return whether HP has reached zero; feedback may still be visible.

        Operation:
            Check the existing zero-HP terminal condition.
        Input:
            Current hp; feedback may still be visible.
        Output:
            Returns bool without changing the stage.
        """
        return self.hp == 0

    @property
    def tint_alpha(self):
        """Return the current mistake tint opacity with zero-duration protection.

        Operation:
            Scale mistake opacity by its remaining duration, handling zero duration.
        Input:
            tint_remaining seconds and configured tint duration/alpha.
        Output:
            Returns integer alpha; zero duration returns zero.
        """
        if s.MISTAKE_TINT_DURATION <= 0:
            return 0
        return round(s.MISTAKE_TINT_ALPHA * self.tint_remaining / s.MISTAKE_TINT_DURATION)

    @property
    def objection_progress(self):
        """Return the legacy normalized progress for external callers.

        Operation:
            Normalize the remaining correct-effect clock for legacy callers. The shared
            ribbon uses banner_elapsed; this compatibility property retains the public
            OBJECTION_DURATION normalization.
        Input:
            animation_remaining and public OBJECTION_DURATION seconds.
        Output:
            Returns progress capped at one; ribbon drawing still uses banner_elapsed.
        """
        return min(1, 1-self.animation_remaining / max(.001, s.OBJECTION_DURATION))

    def next_round(self):
        """Prepare hidden targets and clear per-round result and animation state.

        Operation:
            Unlock content, select a question/choices, build hidden targets, and reset
            round state.
        Input:
            Session number/HP/unlocks, bank RNG/content, and settings.
        Output:
            Advances the round and sets READING with cleared clocks/guards; zero HP
            returns without changes.
        """
        if self.game_over:
            return
        # Operation: Unlocking rebuilds eligible content before target initialization
        #     consumes RNG.
        # Input: Next round number, schedule, bank, and RNG.
        # Output: Unlocked pool, selected question/choices, then hidden targets in
        #     original RNG order.
        self.number += 1
        unlocked = unlocked_at(self.schedule, self.number)
        self.new_fallacies = tuple(id_ for id_ in unlocked if id_ not in self.unlocked) if self.number > 1 else ()
        self.unlocked = unlocked
        self.question = self.bank.draw(self.unlocked)
        self.choices = self.bank.choices(self.question.fallacy, self.unlocked)
        self.targets = make_targets(self.choices, self.bank.fallacies, self.bank.rng)
        # Operation: Clear every per-round timer and guard while preserving session
        #     totals.
        # Input: Configured answer time and existing session totals.
        # Output: READING state with fresh clocks/guards while HP/score remain intact.
        self.stage = 'READING'
        self.remaining = s.ANSWER_TIME
        self.animation_remaining = self.tint_remaining = 0.0
        self.transition_remaining = 0.0
        self.result = self.selected = None
        self.resolved = False
        self.tomato_expression = self.expression_for_hp()
        self.gadget_expression, self.chef_expression = 'talking', 'listening'

    def expression_for_hp(self):
        """Return the shared Tomato expression selected from current HP.

        Operation:
            Delegate current HP to the shared Tomato expression selector.
        Input:
            Current hp and shared expression thresholds.
        Output:
            Returns an expression name without changing HP.
        """
        return tomato_expression_for_hp(self.hp)

    def acknowledge_unlock(self):
        """Dismiss the untimed unlock card without starting the answer timer.

        Operation:
            Dismiss the untimed new-fallacy card.
        Input:
            Current new_fallacies state.
        Output:
            Sets new_fallacies to an empty tuple; returns None.
        """
        self.new_fallacies = ()

    def ready(self):
        """Start board entrance only from reading after unlock acknowledgment.

        Operation:
            Enter the board transition only after the unlock card is acknowledged.
        Input:
            Current stage/new_fallacies and BOARD_ENTER_DURATION seconds.
        Output:
            When allowed, sets BOARD_ENTER, transition clock, and waiting reactions;
            returns None.
        """
        if self.stage == 'READING' and not self.new_fallacies:
            self.stage = 'BOARD_ENTER'
            self.transition_remaining = s.BOARD_ENTER_DURATION
            self.gadget_expression, self.chef_expression = 'waiting', 'listening'

    def answer(self, choice):
        """Resolve a valid visible choice while time remains; return success once.

        Operation:
            Validate active time and choice membership before guarded resolution.
        Input:
            choice ID, ANSWERING stage, remaining seconds, and current choices/question.
        Output:
            Returns True only for a newly resolved valid answer; invalid input returns
            False.
        """
        if self.stage != 'ANSWERING' or self.remaining <= 0 or choice not in self.choices:
            return False
        return self.resolve_round('correct' if choice == self.question.fallacy else 'incorrect', choice)

    def resolve_round(self, result, selected=None):
        """Apply a valid outcome exactly once and freeze movement by changing stage.

        Operation:
            Claim resolution before score/damage, then set one outcome clock and
            reactions.
        Input:
            result: correct/incorrect/timeout; selected: optional fallacy ID; current
            unresolved ANSWERING state.
        Output:
            Updates counters, score or HP, stage, expressions, and feedback markers
            once; returns bool. Invalid active result raises ValueError.
        """
        if self.resolved or self.stage != 'ANSWERING':
            return False
        if result not in self.counts:
            raise ValueError(f'Unknown round result: {result}')
        # Operation: Claim resolution before side effects so repeated input cannot award
        #     or damage twice.
        # Input: Unresolved ANSWERING state and validated result.
        # Output: Claims the guard and records the outcome before awarding points or
        #     damage.
        self.resolved = True
        self.result, self.selected = result, selected
        self.counts[result] += 1
        # Operation: All outcomes now share the requested ribbon clock; reactions retain
        #     their stages.
        # Input: Result, shared phase duration, and current HP/score.
        # Output: Sets one outcome clock and the existing result-specific
        #     stage/reactions.
        self.animation_remaining = self.banner_duration
        if result == 'correct':
            self.score += s.POINTS
            self.stage = 'OBJECTION_ANIMATION'
            self.gadget_expression, self.chef_expression = 'shocked', 'surprised'
        else:
            self.hp = max(0, min(s.START_HP, self.hp - s.DAMAGE))
            self.tint_remaining = s.MISTAKE_TINT_DURATION
            self.stage = 'MISTAKE_ANIMATION'
            self.gadget_expression, self.chef_expression = 'smug', 'stern'
        self.tomato_expression = self.expression_for_hp()
        # Operation: Feedback markers are prepared now but drawn only after the ribbon
        #     exits.
        # Input: Correct fallacy ID, optional selected ID, and current targets.
        # Output: Prepares markers now; the renderer reveals them only in FEEDBACK.
        for target in self.targets:
            target.feedback = ('correct' if target.fallacy_id == self.question.fallacy else
                               'incorrect' if target.fallacy_id == selected else '')
        return True

    @property
    def banner_duration(self):
        """Return shared entrance plus hold plus exit duration in seconds.

        Operation:
            Sum shared entrance, hold, and exit durations.
        Input:
            Configured banner phase durations in seconds.
        Output:
            Returns total seconds without state changes.
        """
        return s.BANNER_IN_DURATION+s.BANNER_HOLD_DURATION+s.BANNER_OUT_DURATION

    @property
    def banner_elapsed(self):
        """Return seconds since the active outcome ribbon began.

        Operation:
            Subtract remaining outcome time from the shared duration.
        Input:
            animation_remaining and banner_duration seconds.
        Output:
            Returns elapsed seconds without state changes.
        """
        return self.banner_duration-self.animation_remaining

    @property
    def board_progress(self):
        """Return normalized board visibility for the current transition stage.

        Operation:
            Normalize entrance/exit clocks into board visibility.
        Input:
            Current stage, transition_remaining, and configured durations.
        Output:
            Returns visibility progress without advancing time.
        """
        if self.stage=='READING':return 0.0
        if self.stage=='BOARD_ENTER':return 1-self.transition_remaining/s.BOARD_ENTER_DURATION
        if self.stage=='BOARD_EXIT':return self.transition_remaining/s.BOARD_EXIT_DURATION
        return 1.0

    def continue_round(self):
        """Begin dismissal only after the outcome animation reveals feedback.

        Operation:
            Begin board dismissal only from visible feedback.
        Input:
            Current stage and BOARD_EXIT_DURATION seconds.
        Output:
            When allowed, sets BOARD_EXIT and its clock; returns None.
        """
        if self.stage=='FEEDBACK':
            self.stage='BOARD_EXIT'
            self.transition_remaining=s.BOARD_EXIT_DURATION

    def update(self, dt):
        """Advance the active stage by nonnegative dt seconds.

        Operation:
            Advance only the active stage, resolving timeout once and discarding
            transition overflow.
        Input:
            dt: nonnegative-clamped seconds; stage clocks, targets, and resolution
            guard.
        Output:
            Updates clocks/motion/stages; only ANSWERING moves labels. Exit prepares the
            next round or GAME_OVER; returns None.
        """
        dt=max(0,dt)
        # Operation: Each branch consumes time only in its own stage; no overflow
        #     reaches the next.
        # Input: Current stage and dt clamped to nonnegative seconds.
        # Output: Advances only that stage; transition overflow never consumes
        #     next-stage time.
        if self.stage=='BOARD_ENTER':
            self.transition_remaining=max(0,self.transition_remaining-dt)
            if self.transition_remaining<=1e-8:
                self.stage='ANSWERING'
                self.transition_remaining=0
                self.remaining=s.ANSWER_TIME
        elif self.stage=='ANSWERING':
            # Operation: Move only during the remaining answer interval, then resolve
            #     timeout once.
            # Input: Remaining answer seconds, dt, and target state.
            # Output: Integrates the active interval, reduces the timer, and resolves
            #     timeout once.
            active_dt=min(dt,self.remaining)
            update_targets(self.targets,active_dt)
            self.remaining=max(0,self.remaining-dt)
            if self.remaining<=1e-8:
                self.remaining=0
                self.resolve_round('timeout')
        elif self.stage in ('OBJECTION_ANIMATION','MISTAKE_ANIMATION'):
            self.animation_remaining=max(0,self.animation_remaining-dt)
            self.tint_remaining=max(0,self.tint_remaining-dt)
            if self.animation_remaining<=1e-8:
                self.animation_remaining=0
                self.stage='FEEDBACK'
        elif self.stage=='FEEDBACK':
            self.tint_remaining=max(0,self.tint_remaining-dt)
        elif self.stage=='BOARD_EXIT':
            self.transition_remaining=max(0,self.transition_remaining-dt)
            if self.transition_remaining<=1e-8:
                if self.game_over:self.stage='GAME_OVER'
                else:self.next_round()
