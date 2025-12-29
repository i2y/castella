from enum import Enum


# Legacy COLOR_SCHEMA - kept for backward compatibility
# New code should use castella.theme.DARK_PALETTE / LIGHT_PALETTE
COLOR_SCHEMA = (
    # Castella Dark Theme
    {
        "bg-canvas": "#1e1e1e",
        "bg-primary": "#1e1e1e",
        "bg-secondary": "#1e1e1e",
        "bg-tertiary": "#282a36",  # Dark background
        "bg-overlay": "#ff79c6",  # Neon pink
        "bg-info": "#1e1e1e",
        "bg-danger": "#1e1e1e",
        "bg-success": "#1e1e1e",
        "bg-warning": "#1e1e1e",
        "bg-pushed": "#1e1e1e",
        "bg-selected": "#ff79c6",  # Neon pink
        "fg": "#f8f8f2",  # Light foreground
        "text-primary": "#f8f8f2",
        "text-info": "#00ffff",  # Neon cyan
        "text-danger": "#ff6347",  # Neon red
        "text-success": "#32cd32",  # Neon green
        "text-warning": "#ffd700",  # Neon yellow
        "border-primary": "#bd93f9",  # Neon purple
        "border-secondary": "#ff79c6",  # Neon pink
        "border-info": "#00ffff",  # Neon cyan
        "border-danger": "#ff6347",  # Neon red
        "border-success": "#32cd32",  # Neon green
        "border-warning": "#ffd700",  # Neon yellow
    },
    # Castella Unicorn Light Theme
    {
        "bg-canvas": "#fff0f6",  # Very light pink background
        "bg-primary": "#fff0f6",  # Same as canvas
        "bg-secondary": "#fce4ec",  # Light pink
        "bg-tertiary": "#e8eaf6",  # Light lavender
        "bg-overlay": "#ffccf9",  # Light pink overlay
        "bg-info": "#e1f5fe",  # Light cyan background for info
        "bg-danger": "#fce4ec",  # Light pink background for danger
        "bg-success": "#e8f5e9",  # Light green background for success
        "bg-warning": "#fff9c4",  # Light yellow background for warning
        "bg-pushed": "#f8bbd0",  # Slightly darker pink when pushed
        "bg-selected": "#f8bbd0",  # Slightly darker pink for selection
        "fg": "#212121",  # Dark text
        "text-primary": "#212121",  # Dark text
        "text-info": "#7e57c2",  # Purple text
        "text-danger": "#ec407a",  # Pink text
        "text-success": "#66bb6a",  # Light green text
        "text-warning": "#ffb300",  # Amber text
        "border-primary": "#ba68c8",  # Light purple border
        "border-secondary": "#f48fb1",  # Light pink border
        "border-info": "#81d4fa",  # Light blue border
        "border-danger": "#f06292",  # Pink border
        "border-success": "#a5d6a7",  # Light green border
        "border-warning": "#ffcc80",  # Light orange border
    },
)


class PredefinedSchema(Enum):
    DARK = 0
    LIGHT = 1
