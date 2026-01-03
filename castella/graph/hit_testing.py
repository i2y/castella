"""Hit testing utilities for graph canvas interactions."""

from __future__ import annotations

from dataclasses import dataclass

from castella.models.geometry import Point, Rect


@dataclass(slots=True)
class GraphNodeElement:
    """A hit-testable node region.

    Represents a node's bounding rectangle for mouse interaction
    detection.

    Attributes:
        rect: Bounding rectangle in screen coordinates.
        node_id: ID of the node this element represents.
    """

    rect: Rect
    node_id: str

    def contains(self, point: Point) -> bool:
        """Check if the point is within this node's bounds.

        Args:
            point: Point to test in screen coordinates.

        Returns:
            True if point is inside the node.
        """
        return self.rect.contain(point)

    @property
    def center(self) -> Point:
        """Get the center point of this element."""
        return self.rect.center


@dataclass(slots=True)
class GraphEdgeElement:
    """A hit-testable edge region.

    Represents an edge as a series of points along its path
    for mouse interaction detection.

    Attributes:
        points: List of points along the edge path.
        thickness: Hit test thickness around the line.
        edge_id: ID of the edge this element represents.
    """

    points: list[Point]
    thickness: float
    edge_id: str

    def contains(self, point: Point) -> bool:
        """Check if the point is near this edge.

        Tests if the point is within the thickness distance of
        any segment along the edge path.

        Args:
            point: Point to test in screen coordinates.

        Returns:
            True if point is within thickness of the edge.
        """
        for i in range(len(self.points) - 1):
            if self._point_near_segment(point, self.points[i], self.points[i + 1]):
                return True
        return False

    def _point_near_segment(self, p: Point, a: Point, b: Point) -> bool:
        """Check if point is within thickness of line segment.

        Uses point-to-line-segment distance calculation with
        projection onto the segment.

        Args:
            p: Point to test.
            a: Start of segment.
            b: End of segment.

        Returns:
            True if point is near the segment.
        """
        # Vector from a to b
        ab_x = b.x - a.x
        ab_y = b.y - a.y

        # Vector from a to p
        ap_x = p.x - a.x
        ap_y = p.y - a.y

        # Length squared of segment
        ab_len_sq = ab_x * ab_x + ab_y * ab_y
        if ab_len_sq == 0:
            # Segment is a point
            dist_sq = ap_x * ap_x + ap_y * ap_y
            return dist_sq <= self.thickness * self.thickness

        # Project p onto line ab, clamped to segment
        t = max(0, min(1, (ap_x * ab_x + ap_y * ab_y) / ab_len_sq))

        # Closest point on segment
        closest_x = a.x + t * ab_x
        closest_y = a.y + t * ab_y

        # Distance to closest point
        dx = p.x - closest_x
        dy = p.y - closest_y
        dist_sq = dx * dx + dy * dy

        return dist_sq <= self.thickness * self.thickness


def hit_test(
    elements: list[GraphNodeElement | GraphEdgeElement], point: Point
) -> GraphNodeElement | GraphEdgeElement | None:
    """Find element at point.

    Tests elements in reverse order so topmost elements are found first.
    Nodes are typically added after edges, so this ensures nodes
    take priority over edges for hit testing.

    Args:
        elements: List of elements to test.
        point: Point to test.

    Returns:
        The hit element or None if no hit.
    """
    for element in reversed(elements):
        if element.contains(point):
            return element
    return None
