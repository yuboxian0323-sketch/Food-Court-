"""The explicit Section 5.7 unlock schedule, validated against content."""
import json
from systems.question_bank import ContentError


def load_schedule(path, fallacies):
    try:
        rows = json.loads(path.read_text(encoding='utf-8'))['schedule']
        if not isinstance(rows, list) or not rows:
            raise ValueError('schedule must be a non-empty list')
        previous, seen = 0, set()
        schedule = []
        for row in rows:
            number, ids = row['question'], row['unlock']
            if type(number) is not int or number <= previous:
                raise ValueError('question thresholds must be increasing positive integers')
            if not isinstance(ids, list) or not ids:
                raise ValueError('each threshold needs a non-empty unlock list')
            for id_ in ids:
                if not isinstance(id_, str) or id_ not in fallacies or id_ in seen:
                    raise ValueError(f'duplicate or unknown fallacy: {id_}')
                seen.add(id_)
            schedule.append((number, tuple(ids)))
            previous = number
        if schedule[0][0] != 1 or len(schedule[0][1]) != 2:
            raise ValueError('start at question 1 with two fallacies')
        if seen != set(fallacies):
            raise ValueError('schedule must unlock every fallacy')
        return tuple(schedule)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ContentError(f'difficulty.json: {error}') from error


def unlocked_at(schedule, number):
    return tuple(id_ for threshold, ids in schedule if number >= threshold for id_ in ids)
