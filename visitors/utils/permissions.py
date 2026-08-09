"""Permission helpers for visitor views."""

from visitors.models import Visitor


class IsVisitorOwner:
    """Permission class: user must own the visitor request."""

    def __init__(self, user: object, visitor: Visitor) -> None:
        self.user = user
        self.visitor = visitor

    def has_permission(self) -> bool:
        return self.visitor.created_by == self.user or (
            hasattr(self.visitor, "building")
            and self.visitor.building.owner == self.user
        )


class CanApproveVisitor:
    """Permission class: user must be building owner or have approval rights."""

    def __init__(self, user: object, visitor: Visitor) -> None:
        self.user = user
        self.visitor = visitor

    def has_permission(self) -> bool:
        return self.visitor.building.owner == self.user


class CanCheckInVisitor:
    """Permission class: caretaker or building owner can check in."""

    def __init__(self, user: object, visitor: Visitor) -> None:
        self.user = user
        self.visitor = visitor

    def has_permission(self) -> bool:
        return self.visitor.building.owner == self.user


class CanCheckOutVisitor:
    """Permission class: caretaker or building owner can check out."""

    def __init__(self, user: object, visitor: Visitor) -> None:
        self.user = user
        self.visitor = visitor

    def has_permission(self) -> bool:
        return self.visitor.building.owner == self.user
