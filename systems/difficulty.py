"""The explicit Section 5.7 unlock schedule, validated against content.

Operation:
    Validate ordered unlock thresholds and derive eligible topic IDs.
Input:
    Difficulty JSON, valid fallacy IDs, and one-based question numbers.
Output:
    Immutable validated schedule/ID tuples, or ContentError diagnostics.
"""
import json
from systems.question_bank import ContentError


def load_schedule(path, fallacies):
    """Read and validate ordered unlock thresholds against the fallacy mapping.

    Operation:
        Validate monotonic thresholds, unique topics, and full content coverage.
    Input:
        path: JSON schedule; fallacies: valid ID mapping.
    Output:
        Returns immutable threshold/ID tuples; raises ContentError for file or
        validation failures.
    """
    try:
        rows = json.loads(path.read_text(encoding='utf-8'))['schedule']
        if not isinstance(rows, list) or not rows:
            raise ValueError('schedule must be a non-empty list')
        previous, seen = 0, set()
        schedule = []
        # Operation: Enforce monotonic thresholds and exactly one introduction for every
        #     topic.
        # Input: Schedule rows, valid fallacy IDs, and previously seen topics.
        # Output: Validated increasing thresholds with each topic introduced once.
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
    """Return IDs unlocked by the supplied one-based question number, in order.

    Operation:
        Flatten thresholds reached by the current question in schedule order.
    Input:
        schedule and number: one-based question number.
    Output:
        Returns a tuple of unlocked IDs without state changes.
    """
    return tuple(id_ for threshold, ids in schedule if number >= threshold for id_ in ids)
