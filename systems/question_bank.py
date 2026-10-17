"""Validate editable content and draw questions without replacement."""
import json
import random
from dataclasses import dataclass


class ContentError(ValueError):
    pass


@dataclass(frozen=True)
class Question:
    id: str
    fallacy: str
    argument: str
    explanation: str


def read_json(path, key):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise ContentError(f'{path.name}: {error}') from error
    if not isinstance(value, dict) or not isinstance(value.get(key), list) or not value[key]:
        raise ContentError(f'{path.name}: expected a non-empty "{key}" list.')
    return value[key]


class QuestionBank:
    def __init__(self, data_dir, rng=None):
        self.rng = rng or random.Random()
        self.fallacies = {}
        for row in read_json(data_dir / 'fallacies.json', 'fallacies'):
            if not isinstance(row, dict):
                raise ContentError('fallacies.json: each entry must be an object.')
            for key in ('id', 'name', 'definition', 'example'):
                if not isinstance(row.get(key), str) or not row[key].strip():
                    raise ContentError(f'fallacies.json: missing or invalid {key}.')
            if row['id'] in self.fallacies:
                raise ContentError(f'fallacies.json: duplicate id {row["id"]}.')
            self.fallacies[row['id']] = dict(row)
        if not 2 <= len(self.fallacies) <= 18:
            raise ContentError('fallacies.json: expected 2–18 fallacies.')
        questions, ids = [], set()
        for row in read_json(data_dir / 'questions.json', 'questions'):
            if not isinstance(row, dict):
                raise ContentError('questions.json: each entry must be an object.')
            label = row.get('id', '<missing id>')
            for key, limit in (('id', 80), ('argument', 220), ('explanation', 260)):
                if not isinstance(row.get(key), str) or not 1 <= len(row[key].strip()) <= limit:
                    raise ContentError(f'questions.json: {label}: {key} must be 1–{limit} characters.')
            if row['id'] in ids:
                raise ContentError(f'questions.json: duplicate id {label}.')
            ids.add(row['id'])
            if not isinstance(row.get('fallacy'), str) or row['fallacy'] not in self.fallacies:
                raise ContentError(f'questions.json: {label}: unknown fallacy.')
            if 'choices' in row:
                choices = row['choices']
                if (not isinstance(choices, list) or not 2 <= len(choices) <= 8
                        or any(not isinstance(c, str) or c not in self.fallacies for c in choices)
                        or len(set(choices)) != len(choices) or row['fallacy'] not in choices):
                    raise ContentError(f'questions.json: {label}: choices need 2–8 unique valid IDs including the answer.')
            questions.append(Question(*(row[k] for k in ('id', 'fallacy', 'argument', 'explanation'))))
        if set(q.fallacy for q in questions) != set(self.fallacies):
            raise ContentError('questions.json: provide questions for every fallacy.')
        self.questions = tuple(questions)
        self.reset()

    def reset(self):
        self._bag = []
        self._last = None
        self._eligible = None

    def draw(self, unlocked=None):
        eligible = frozenset(unlocked if unlocked is not None else self.fallacies)
        if eligible != self._eligible:
            self._bag = []
            self._eligible = eligible
        if not self._bag:
            self._bag = [q for q in self.questions if q.fallacy in eligible]
            if not self._bag:
                raise ContentError('questions.json: no eligible questions for unlocked fallacies.')
            self.rng.shuffle(self._bag)
            if len(self._bag) > 1 and self._bag[-1].id == self._last:
                self._bag[0], self._bag[-1] = self._bag[-1], self._bag[0]
        question = self._bag.pop()
        self._last = question.id
        return question

    def choices(self, answer, unlocked):
        # Legacy stored choices are validated, but progression determines what
        # can be offered. A stored distractor must never expose a locked topic.
        distractors = [id_ for id_ in unlocked if id_ != answer]
        choices = [answer] + self.rng.sample(distractors, min(7, len(distractors)))
        self.rng.shuffle(choices)
        return choices
