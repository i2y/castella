"""Shape drawing primitives for Mermaid diagrams."""

import math

from castella.core import (
    Circle,
    FillStyle,
    Painter,
    Point,
    Rect,
    Size,
    StrokeStyle,
    Style,
)
from castella.models.font import Font

from .models import ArrowType, LineType, NodeShape


def draw_node(
    p: Painter,
    x: float,
    y: float,
    width: float,
    height: float,
    shape: NodeShape,
    label: str,
    fill_color: str,
    stroke_color: str,
    text_color: str,
    font_family: str,
    font_size: int,
) -> None:
    """Draw a diagram node with the specified shape."""
    if shape == NodeShape.RECT:
        _draw_rect(p, x, y, width, height, fill_color, stroke_color)
    elif shape == NodeShape.ROUNDED:
        _draw_rounded_rect(p, x, y, width, height, fill_color, stroke_color)
    elif shape == NodeShape.STADIUM:
        _draw_stadium(p, x, y, width, height, fill_color, stroke_color)
    elif shape == NodeShape.CIRCLE:
        _draw_circle(p, x, y, width, height, fill_color, stroke_color)
    elif shape == NodeShape.DOUBLE_CIRCLE:
        _draw_double_circle(p, x, y, width, height, fill_color, stroke_color)
    elif shape == NodeShape.DIAMOND:
        _draw_diamond(p, x, y, width, height, fill_color, stroke_color)
    elif shape == NodeShape.HEXAGON:
        _draw_hexagon(p, x, y, width, height, fill_color, stroke_color)
    elif shape == NodeShape.CYLINDER:
        _draw_cylinder(p, x, y, width, height, fill_color, stroke_color)
    elif shape == NodeShape.SUBROUTINE:
        _draw_subroutine(p, x, y, width, height, fill_color, stroke_color)
    elif shape in (NodeShape.START, NodeShape.END):
        _draw_state_circle(
            p,
            x,
            y,
            width,
            height,
            fill_color,
            stroke_color,
            is_end=(shape == NodeShape.END),
        )
    else:
        _draw_rect(p, x, y, width, height, fill_color, stroke_color)

    # Draw label (centered)
    if label:
        text_style = Style(
            fill=FillStyle(color=text_color),
            font=Font(family=font_family, size=font_size),
        )
        p.style(text_style)
        text_x = x + width / 2 - len(label) * font_size * 0.3
        text_y = y + height / 2 + font_size / 3
        p.fill_text(label, Point(x=text_x, y=text_y), width)


def _draw_rect(
    p: Painter, x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> None:
    """Draw a rectangle."""
    rect = Rect(origin=Point(x=x, y=y), size=Size(width=w, height=h))

    # Fill
    p.style(Style(fill=FillStyle(color=fill)))
    p.fill_rect(rect)

    # Stroke
    p.style(Style(stroke=StrokeStyle(color=stroke)))
    p.stroke_rect(rect)


def _draw_rounded_rect(
    p: Painter, x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> None:
    """Draw a rounded rectangle with rounded corners."""
    radius = min(8, w / 4, h / 4)  # Corner radius

    # Fill main body (rectangles + corner circles)
    p.style(Style(fill=FillStyle(color=fill)))

    # Center rectangle (full width, reduced height)
    center_rect = Rect(
        origin=Point(x=x, y=y + radius),
        size=Size(width=w, height=h - 2 * radius),
    )
    p.fill_rect(center_rect)

    # Top rectangle (reduced width)
    top_rect = Rect(
        origin=Point(x=x + radius, y=y),
        size=Size(width=w - 2 * radius, height=radius),
    )
    p.fill_rect(top_rect)

    # Bottom rectangle (reduced width)
    bottom_rect = Rect(
        origin=Point(x=x + radius, y=y + h - radius),
        size=Size(width=w - 2 * radius, height=radius),
    )
    p.fill_rect(bottom_rect)

    # Fill corner circles
    corners = [
        (x + radius, y + radius),  # top-left
        (x + w - radius, y + radius),  # top-right
        (x + radius, y + h - radius),  # bottom-left
        (x + w - radius, y + h - radius),  # bottom-right
    ]
    for cx, cy in corners:
        p.fill_circle(Circle(center=Point(x=cx, y=cy), radius=radius))

    # Draw outline edges
    _draw_solid_line(p, x + radius, y, x + w - radius, y, stroke, width=1.0)  # Top
    _draw_solid_line(
        p, x + radius, y + h, x + w - radius, y + h, stroke, width=1.0
    )  # Bottom
    _draw_solid_line(p, x, y + radius, x, y + h - radius, stroke, width=1.0)  # Left
    _draw_solid_line(
        p, x + w, y + radius, x + w, y + h - radius, stroke, width=1.0
    )  # Right

    # Corner arcs (approximated with circles)
    p.style(Style(fill=FillStyle(color=stroke)))
    arc_steps = 12
    for i in range(arc_steps + 1):
        angle = math.pi / 2 * i / arc_steps
        # Top-left corner
        px = x + radius - radius * math.cos(angle)
        py = y + radius - radius * math.sin(angle)
        p.fill_circle(Circle(center=Point(x=px, y=py), radius=1.0))
        # Top-right corner
        px = x + w - radius + radius * math.cos(angle)
        py = y + radius - radius * math.sin(angle)
        p.fill_circle(Circle(center=Point(x=px, y=py), radius=1.0))
        # Bottom-left corner
        px = x + radius - radius * math.cos(angle)
        py = y + h - radius + radius * math.sin(angle)
        p.fill_circle(Circle(center=Point(x=px, y=py), radius=1.0))
        # Bottom-right corner
        px = x + w - radius + radius * math.cos(angle)
        py = y + h - radius + radius * math.sin(angle)
        p.fill_circle(Circle(center=Point(x=px, y=py), radius=1.0))


def _draw_stadium(
    p: Painter, x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> None:
    """Draw a stadium shape (pill)."""
    # Simplified as rounded rect
    _draw_rounded_rect(p, x, y, w, h, fill, stroke)


def _draw_circle(
    p: Painter, x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> None:
    """Draw a circle using Painter's native circle methods."""
    cx = x + w / 2
    cy = y + h / 2
    radius = min(w, h) / 2

    center = Point(x=cx, y=cy)
    circle = Circle(center=center, radius=radius)

    # Fill
    p.style(Style(fill=FillStyle(color=fill)))
    p.fill_circle(circle)

    # Stroke
    p.style(Style(stroke=StrokeStyle(color=stroke)))
    p.stroke_circle(circle)


def _draw_double_circle(
    p: Painter, x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> None:
    """Draw a double circle (for end states)."""
    _draw_circle(p, x, y, w, h, fill, stroke)
    # Inner circle
    margin = 4
    _draw_circle(
        p, x + margin, y + margin, w - 2 * margin, h - 2 * margin, fill, stroke
    )


def _draw_diamond(
    p: Painter, x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> None:
    """Draw a diamond (rhombus) shape."""
    # Calculate diamond vertices
    cx = x + w / 2  # center x
    cy = y + h / 2  # center y

    # Diamond points: top, right, bottom, left
    top = (cx, y)
    right = (x + w, cy)
    bottom = (cx, y + h)
    left = (x, cy)

    # Fill diamond by drawing filled triangles using horizontal lines
    p.style(Style(fill=FillStyle(color=fill)))

    # Draw filled diamond using horizontal line segments
    for dy in range(int(h) + 1):
        progress = dy / h if h > 0 else 0
        if progress <= 0.5:
            # Upper half: width increases
            half_width = (progress * 2) * (w / 2)
        else:
            # Lower half: width decreases
            half_width = ((1 - progress) * 2) * (w / 2)

        if half_width > 0:
            line_y = y + dy
            line_x = cx - half_width
            line_rect = Rect(
                origin=Point(x=line_x, y=line_y),
                size=Size(width=half_width * 2, height=1),
            )
            p.fill_rect(line_rect)

    # Draw diamond border (4 edges)
    p.style(Style(stroke=StrokeStyle(color=stroke)))
    _draw_solid_line(p, top[0], top[1], right[0], right[1], stroke)
    _draw_solid_line(p, right[0], right[1], bottom[0], bottom[1], stroke)
    _draw_solid_line(p, bottom[0], bottom[1], left[0], left[1], stroke)
    _draw_solid_line(p, left[0], left[1], top[0], top[1], stroke)


def _draw_hexagon(
    p: Painter, x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> None:
    """Draw a hexagon."""
    # Simplified as rect
    _draw_rect(p, x, y, w, h, fill, stroke)


def _draw_cylinder(
    p: Painter, x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> None:
    """Draw a cylinder (database)."""
    # Simplified as rect with top/bottom ellipse representation
    _draw_rect(p, x, y, w, h, fill, stroke)

    # Add top "ellipse" as a small rect
    ellipse_height = 8
    top_rect = Rect(
        origin=Point(x=x, y=y),
        size=Size(width=w, height=ellipse_height),
    )
    p.style(Style(stroke=StrokeStyle(color=stroke)))
    p.stroke_rect(top_rect)


def _draw_subroutine(
    p: Painter, x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> None:
    """Draw a subroutine box (double vertical lines)."""
    _draw_rect(p, x, y, w, h, fill, stroke)

    # Add inner vertical lines
    margin = 8
    p.style(Style(stroke=StrokeStyle(color=stroke)))

    # Left line
    left_line = Rect(
        origin=Point(x=x + margin, y=y),
        size=Size(width=1, height=h),
    )
    p.fill_rect(left_line)

    # Right line
    right_line = Rect(
        origin=Point(x=x + w - margin, y=y),
        size=Size(width=1, height=h),
    )
    p.fill_rect(right_line)


def _draw_state_circle(
    p: Painter,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    stroke: str,
    is_end: bool = False,
) -> None:
    """Draw a state diagram start/end circle using native circle methods."""
    diameter = min(w, h)
    cx = x + diameter / 2
    cy = y + diameter / 2
    radius = diameter / 2

    center = Point(x=cx, y=cy)

    if is_end:
        # End state: outer circle with inner filled circle
        outer_circle = Circle(center=center, radius=radius)

        # Draw outer circle outline
        p.style(Style(stroke=StrokeStyle(color=stroke)))
        p.stroke_circle(outer_circle)

        # Draw inner filled circle
        inner_circle = Circle(center=center, radius=radius * 0.6)
        p.style(Style(fill=FillStyle(color=stroke)))
        p.fill_circle(inner_circle)
    else:
        # Start state: solid filled circle
        circle = Circle(center=center, radius=radius)
        p.style(Style(fill=FillStyle(color=stroke)))
        p.fill_circle(circle)


def draw_edge(
    p: Painter,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    line_type: LineType,
    arrow_type: ArrowType,
    arrow_start: bool,
    arrow_end: bool,
    label: str,
    stroke_color: str,
    text_color: str,
    font_family: str,
    font_size: int,
) -> None:
    """Draw an edge between two points."""
    # Draw line
    if line_type == LineType.DASHED:
        _draw_dashed_line(p, x1, y1, x2, y2, stroke_color)
    elif line_type == LineType.DOTTED:
        _draw_dotted_line(p, x1, y1, x2, y2, stroke_color)
    elif line_type == LineType.THICK:
        _draw_thick_line(p, x1, y1, x2, y2, stroke_color)
    else:
        _draw_solid_line(p, x1, y1, x2, y2, stroke_color)

    # Draw arrowheads
    if arrow_end and arrow_type != ArrowType.OPEN:
        _draw_arrowhead(p, x1, y1, x2, y2, arrow_type, stroke_color)

    if arrow_start and arrow_type != ArrowType.OPEN:
        _draw_arrowhead(p, x2, y2, x1, y1, arrow_type, stroke_color)

    # Draw label
    if label:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        # Background for label
        label_width = len(label) * font_size * 0.6
        label_height = font_size + 4
        bg_rect = Rect(
            origin=Point(x=mid_x - label_width / 2, y=mid_y - label_height / 2),
            size=Size(width=label_width, height=label_height),
        )
        p.style(Style(fill=FillStyle(color="#ffffff")))
        p.fill_rect(bg_rect)

        # Label text
        text_style = Style(
            fill=FillStyle(color=text_color),
            font=Font(family=font_family, size=font_size - 2),
        )
        p.style(text_style)
        p.fill_text(
            label,
            Point(x=mid_x - len(label) * font_size * 0.25, y=mid_y + font_size / 3),
            None,
        )


def _draw_solid_line(
    p: Painter,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str,
    width: float = 1.5,
) -> None:
    """Draw a solid line using anti-aliased circles."""
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)

    if length < 0.5:
        return

    # Draw as a series of circles along the line (anti-aliased)
    p.style(Style(fill=FillStyle(color=color)))
    steps = max(2, int(length / 1.5))
    for i in range(steps + 1):
        t = i / steps
        x = x1 + dx * t
        y = y1 + dy * t
        p.fill_circle(Circle(center=Point(x=x, y=y), radius=width))


def _draw_dashed_line(
    p: Painter, x1: float, y1: float, x2: float, y2: float, color: str
) -> None:
    """Draw a dashed line."""
    dx = x2 - x1
    dy = y2 - y1
    length = (dx**2 + dy**2) ** 0.5

    if length < 1:
        return

    dash_length = 8
    gap_length = 4
    pattern_length = dash_length + gap_length

    steps = int(length / pattern_length)
    for i in range(steps):
        t1 = (i * pattern_length) / length
        t2 = min((i * pattern_length + dash_length) / length, 1.0)

        sx = x1 + dx * t1
        sy = y1 + dy * t1
        ex = x1 + dx * t2
        ey = y1 + dy * t2

        _draw_solid_line(p, sx, sy, ex, ey, color)


def _draw_dotted_line(
    p: Painter, x1: float, y1: float, x2: float, y2: float, color: str
) -> None:
    """Draw a dotted line using anti-aliased circles."""
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)

    if length < 1:
        return

    p.style(Style(fill=FillStyle(color=color)))
    dot_spacing = 6
    steps = max(1, int(length / dot_spacing))

    for i in range(steps + 1):
        t = i / steps if steps > 0 else 0
        x = x1 + dx * t
        y = y1 + dy * t
        p.fill_circle(Circle(center=Point(x=x, y=y), radius=1.5))


def _draw_thick_line(
    p: Painter, x1: float, y1: float, x2: float, y2: float, color: str
) -> None:
    """Draw a thick line using larger radius circles."""
    _draw_solid_line(p, x1, y1, x2, y2, color, width=3.0)


def _draw_arrowhead(
    p: Painter,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    arrow_type: ArrowType,
    color: str,
) -> None:
    """Draw an arrowhead at (x2, y2) pointing from (x1, y1)."""
    dx = x2 - x1
    dy = y2 - y1
    length = (dx**2 + dy**2) ** 0.5

    if length < 1:
        return

    # Normalize direction
    dx /= length
    dy /= length

    # Arrow dimensions
    arrow_length = 10
    arrow_width = 6

    # Arrow tip is at (x2, y2)
    tip_x = x2
    tip_y = y2

    # Base of arrow
    base_x = x2 - dx * arrow_length
    base_y = y2 - dy * arrow_length

    # Perpendicular direction
    perp_x = -dy
    perp_y = dx

    # Arrow points
    left_x = base_x + perp_x * arrow_width / 2
    left_y = base_y + perp_y * arrow_width / 2
    right_x = base_x - perp_x * arrow_width / 2
    right_y = base_y - perp_y * arrow_width / 2

    # Draw arrow as filled triangles (using small rects)
    p.style(Style(fill=FillStyle(color=color)))

    if arrow_type == ArrowType.ARROW:
        # Filled arrow
        # Draw lines from tip to base corners
        _draw_solid_line(p, tip_x, tip_y, left_x, left_y, color)
        _draw_solid_line(p, tip_x, tip_y, right_x, right_y, color)
        _draw_solid_line(p, left_x, left_y, right_x, right_y, color)

    elif arrow_type == ArrowType.CIRCLE:
        # Circle at end
        circle_size = 6
        rect = Rect(
            origin=Point(x=x2 - circle_size / 2, y=y2 - circle_size / 2),
            size=Size(width=circle_size, height=circle_size),
        )
        p.fill_rect(rect)

    elif arrow_type == ArrowType.CROSS:
        # X at end
        cross_size = 6
        _draw_solid_line(
            p,
            x2 - cross_size / 2,
            y2 - cross_size / 2,
            x2 + cross_size / 2,
            y2 + cross_size / 2,
            color,
        )
        _draw_solid_line(
            p,
            x2 - cross_size / 2,
            y2 + cross_size / 2,
            x2 + cross_size / 2,
            y2 - cross_size / 2,
            color,
        )


def draw_class_box(
    p: Painter,
    x: float,
    y: float,
    width: float,
    height: float,
    name: str,
    attributes: list[str],
    methods: list[str],
    fill_color: str,
    stroke_color: str,
    text_color: str,
    font_family: str,
    font_size: int,
) -> None:
    """Draw a UML class box."""
    # Draw outer rectangle
    rect = Rect(origin=Point(x=x, y=y), size=Size(width=width, height=height))

    p.style(Style(fill=FillStyle(color=fill_color)))
    p.fill_rect(rect)

    p.style(Style(stroke=StrokeStyle(color=stroke_color)))
    p.stroke_rect(rect)

    line_height = font_size + 4
    padding = 8
    current_y = y + padding

    # Draw class name (bold, centered)
    text_style = Style(
        fill=FillStyle(color=text_color),
        font=Font(family=font_family, size=font_size),
    )
    p.style(text_style)

    name_x = x + width / 2 - len(name) * font_size * 0.3
    p.fill_text(name, Point(x=name_x, y=current_y + font_size), width - padding * 2)
    current_y += line_height + padding

    # Separator line
    if attributes or methods:
        separator = Rect(
            origin=Point(x=x, y=current_y),
            size=Size(width=width, height=1),
        )
        p.style(Style(fill=FillStyle(color=stroke_color)))
        p.fill_rect(separator)
        current_y += padding

    # Draw attributes
    attr_style = Style(
        fill=FillStyle(color=text_color),
        font=Font(family=font_family, size=font_size - 2),
    )
    p.style(attr_style)

    for attr in attributes:
        p.fill_text(
            attr, Point(x=x + padding, y=current_y + font_size - 2), width - padding * 2
        )
        current_y += line_height - 2

    # Separator between attributes and methods
    if attributes and methods:
        current_y += padding / 2
        separator = Rect(
            origin=Point(x=x, y=current_y),
            size=Size(width=width, height=1),
        )
        p.style(Style(fill=FillStyle(color=stroke_color)))
        p.fill_rect(separator)
        current_y += padding

    # Draw methods
    p.style(attr_style)
    for method in methods:
        p.fill_text(
            method,
            Point(x=x + padding, y=current_y + font_size - 2),
            width - padding * 2,
        )
        current_y += line_height - 2


def draw_sequence_participant(
    p: Painter,
    x: float,
    y: float,
    width: float,
    height: float,
    name: str,
    is_actor: bool,
    fill_color: str,
    stroke_color: str,
    text_color: str,
    font_family: str,
    font_size: int,
) -> None:
    """Draw a sequence diagram participant."""
    if is_actor:
        # Draw stick figure
        _draw_actor(p, x + width / 2, y, stroke_color)
        # Draw name below
        text_style = Style(
            fill=FillStyle(color=text_color),
            font=Font(family=font_family, size=font_size),
        )
        p.style(text_style)
        name_x = x + width / 2 - len(name) * font_size * 0.3
        p.fill_text(name, Point(x=name_x, y=y + height - 5), width)
    else:
        # Draw box
        rect = Rect(origin=Point(x=x, y=y), size=Size(width=width, height=height))

        p.style(Style(fill=FillStyle(color=fill_color)))
        p.fill_rect(rect)

        p.style(Style(stroke=StrokeStyle(color=stroke_color)))
        p.stroke_rect(rect)

        # Draw name (centered)
        text_style = Style(
            fill=FillStyle(color=text_color),
            font=Font(family=font_family, size=font_size),
        )
        p.style(text_style)
        name_x = x + width / 2 - len(name) * font_size * 0.3
        name_y = y + height / 2 + font_size / 3
        p.fill_text(name, Point(x=name_x, y=name_y), width)


def _draw_actor(p: Painter, x: float, y: float, color: str) -> None:
    """Draw a stick figure actor."""
    p.style(Style(fill=FillStyle(color=color)))

    # Head (circle approximation)
    head_size = 10
    head_rect = Rect(
        origin=Point(x=x - head_size / 2, y=y),
        size=Size(width=head_size, height=head_size),
    )
    p.fill_rect(head_rect)

    # Body
    body_start_y = y + head_size
    body_end_y = body_start_y + 15
    _draw_solid_line(p, x, body_start_y, x, body_end_y, color)

    # Arms
    arm_y = body_start_y + 5
    _draw_solid_line(p, x - 10, arm_y, x + 10, arm_y, color)

    # Legs
    _draw_solid_line(p, x, body_end_y, x - 8, body_end_y + 12, color)
    _draw_solid_line(p, x, body_end_y, x + 8, body_end_y + 12, color)


def draw_lifeline(
    p: Painter, x: float, y_start: float, y_end: float, color: str
) -> None:
    """Draw a sequence diagram lifeline (dashed vertical line)."""
    _draw_dashed_line(p, x, y_start, x, y_end, color)


def draw_sequence_message(
    p: Painter,
    x1: float,
    y: float,
    x2: float,
    label: str,
    line_type: LineType,
    arrow_type: ArrowType,
    stroke_color: str,
    text_color: str,
    font_family: str,
    font_size: int,
) -> None:
    """Draw a sequence diagram message arrow."""
    # Draw the line
    if line_type == LineType.DASHED:
        _draw_dashed_line(p, x1, y, x2, y, stroke_color)
    else:
        _draw_solid_line(p, x1, y, x2, y, stroke_color)

    # Draw arrowhead at x2 (always point to the target)
    if arrow_type != ArrowType.OPEN:
        # Arrow always points FROM x1 TO x2
        _draw_arrowhead(p, x1, y, x2, y, arrow_type, stroke_color)

    # Draw label above line
    if label:
        text_style = Style(
            fill=FillStyle(color=text_color),
            font=Font(family=font_family, size=font_size - 2),
        )
        p.style(text_style)
        mid_x = (x1 + x2) / 2
        p.fill_text(label, Point(x=mid_x - len(label) * 3, y=y - 5), None)


def draw_back_edge(
    p: Painter,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    offset: float,
    line_type: LineType,
    arrow_type: ArrowType,
    label: str,
    stroke_color: str,
    text_color: str,
    font_family: str,
    font_size: int,
    source_width: float = 0,
    target_width: float = 0,
    use_right_side: bool = False,
) -> None:
    """Draw a back edge (going upward) with a path around the side.

    Args:
        use_right_side: If True, route around the right side; otherwise left side.
        source_width: Width of source node (needed for right side routing).
        target_width: Width of target node (needed for right side routing).

    The path goes: source -> side -> up/down -> target
    """
    draw_fn = _draw_solid_line
    if line_type == LineType.DASHED:
        draw_fn = _draw_dashed_line
    elif line_type == LineType.DOTTED:
        draw_fn = _draw_dotted_line

    if use_right_side:
        # Route around the right side
        # x1, x2 should be right edges of nodes
        side_x = max(x1 + source_width, x2 + target_width) + offset

        # Segment 1: source right to side
        draw_fn(p, x1 + source_width, y1, side_x, y1, stroke_color)

        # Segment 2: vertical
        draw_fn(p, side_x, y1, side_x, y2, stroke_color)

        # Segment 3: side to target right
        draw_fn(p, side_x, y2, x2 + target_width, y2, stroke_color)

        # Draw arrowhead at target (pointing left)
        if arrow_type != ArrowType.OPEN:
            _draw_arrowhead(
                p, side_x, y2, x2 + target_width, y2, arrow_type, stroke_color
            )

        # Draw label on the vertical segment (right side)
        if label:
            text_style = Style(
                fill=FillStyle(color=text_color),
                font=Font(family=font_family, size=font_size - 2),
            )
            p.style(text_style)
            mid_y = (y1 + y2) / 2
            p.fill_text(label, Point(x=side_x + 5, y=mid_y), None)
    else:
        # Route around the left side
        side_x = min(x1, x2) - offset

        # Segment 1: source left to side
        draw_fn(p, x1, y1, side_x, y1, stroke_color)

        # Segment 2: vertical
        draw_fn(p, side_x, y1, side_x, y2, stroke_color)

        # Segment 3: side to target left
        draw_fn(p, side_x, y2, x2, y2, stroke_color)

        # Draw arrowhead at target (pointing right)
        if arrow_type != ArrowType.OPEN:
            _draw_arrowhead(p, side_x, y2, x2, y2, arrow_type, stroke_color)

        # Draw label on the vertical segment (left side)
        if label:
            text_style = Style(
                fill=FillStyle(color=text_color),
                font=Font(family=font_family, size=font_size - 2),
            )
            p.style(text_style)
            mid_y = (y1 + y2) / 2
            p.fill_text(label, Point(x=side_x - len(label) * 4 - 5, y=mid_y), None)
