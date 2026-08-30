"""
Unit tests for the transition table
Calls the domain function directly, with no database and no HTTP
"""
import pytest

from app.enums import ALLOWED_TRANSITIONS, Status, can_transition


@pytest.mark.parametrize(
    "current,target",
    [
        (Status.OPEN, Status.IN_PROGRESS),
        (Status.IN_PROGRESS, Status.RESOLVED),
        (Status.RESOLVED, Status.CLOSED),
        (Status.RESOLVED, Status.IN_PROGRESS),
    ],
)
def test_permitted_transitions(current, target):
    assert can_transition(current, target) is True


@pytest.mark.parametrize(
    "current,target",
    [
        (Status.OPEN, Status.RESOLVED),
        (Status.OPEN, Status.CLOSED),
        (Status.IN_PROGRESS, Status.CLOSED),
        (Status.CLOSED, Status.OPEN),
        (Status.CLOSED, Status.IN_PROGRESS),
    ],
)
def test_forbidden_transitions(current, target):
    assert can_transition(current, target) is False


def test_closed_is_terminal():
    assert ALLOWED_TRANSITIONS[Status.CLOSED] == frozenset()


def test_closed_is_only_reachable_from_resolved():
    """The structural guarantee behind business rule 4."""
    sources = [s for s, targets in ALLOWED_TRANSITIONS.items() if Status.CLOSED in targets]
    assert sources == [Status.RESOLVED]


def test_every_status_has_a_transition_rule():
    assert set(ALLOWED_TRANSITIONS) == set(Status)