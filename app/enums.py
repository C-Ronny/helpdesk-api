"""
Domain vocabulary: the fixed sets of values a ticket can hold
"""

from enum import Enum

class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Status(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Category(str, Enum):
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    NETWORK = "NETWORK"
    ACCOUNT = "ACCOUNT"
    OTHER = "OTHER"


class Role(str, Enum):
    CUSTOMER = "CUSTOMER"
    AGENT = "AGENT"


# The ticket lifecycle, expressed as a state machine.
#
# Business rule 4 ("a ticket can only be closed after it has been resolved")
# and rule 5 ("invalid status transitions must be rejected") are both enforced
# by this single table: CLOSED is only reachable from RESOLVED, and CLOSED is
# terminal. RESOLVED -> IN_PROGRESS exists so a ticket can be reopened when a
# fix turns out not to have worked.
ALLOWED_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.OPEN: frozenset({Status.IN_PROGRESS}),
    Status.IN_PROGRESS: frozenset({Status.RESOLVED}),
    Status.RESOLVED: frozenset({Status.CLOSED, Status.IN_PROGRESS}),
    Status.CLOSED: frozenset(),
}


def can_transition(current: Status, target: Status) -> bool:
    return target in ALLOWED_TRANSITIONS[current]