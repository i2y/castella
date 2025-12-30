"""Standalone A2UI demo - renders A2UI without needing an agent.

This example demonstrates Castella's A2UI renderer with simulated
data from a restaurant finder agent, showing compatibility with
Google's A2UI legacy format.

Run with:
    uv run python examples/a2ui_standalone_demo.py
"""

from castella import App
from castella.a2ui import A2UIComponent, A2UIRenderer
from castella.frame import Frame


def create_restaurant_ui() -> A2UIComponent:
    """Create A2UI component with restaurant finder data.

    This simulates the response from Google's Restaurant Finder
    sample agent in the legacy A2UI format.
    """
    renderer = A2UIRenderer()

    # beginRendering - starts progressive rendering
    renderer.handle_message({
        "beginRendering": {
            "surfaceId": "default",
            "root": "root-column",
            "styles": {"primaryColor": "#FF0000"}
        }
    })

    # surfaceUpdate - adds components (legacy format with nested component defs)
    renderer.handle_message({
        "surfaceUpdate": {
            "surfaceId": "default",
            "components": [
                # Root column
                {
                    "id": "root-column",
                    "component": {
                        "Column": {
                            "children": {"explicitList": [
                                "title", "subtitle", "divider",
                                "restaurant1", "restaurant2"
                            ]}
                        }
                    }
                },
                # Title
                {
                    "id": "title",
                    "component": {
                        "Text": {
                            "usageHint": "h1",
                            "text": {"literalString": "Top Chinese Restaurants"}
                        }
                    }
                },
                # Subtitle
                {
                    "id": "subtitle",
                    "component": {
                        "Text": {
                            "usageHint": "caption",
                            "text": {"literalString": "New York City"}
                        }
                    }
                },
                # Divider
                {
                    "id": "divider",
                    "component": {
                        "Divider": {}
                    }
                },
                # Restaurant 1 Card
                {
                    "id": "restaurant1",
                    "component": {
                        "Card": {
                            "children": {"explicitList": ["r1-name", "r1-detail", "r1-info"]}
                        }
                    }
                },
                {
                    "id": "r1-name",
                    "component": {
                        "Text": {
                            "usageHint": "h2",
                            "text": {"literalString": "Xi'an Famous Foods"}
                        }
                    }
                },
                {
                    "id": "r1-detail",
                    "component": {
                        "Text": {
                            "text": {"literalString": "Spicy and savory hand-pulled noodles."}
                        }
                    }
                },
                {
                    "id": "r1-info",
                    "component": {
                        "Row": {
                            "children": {"explicitList": ["r1-rating", "r1-address"]}
                        }
                    }
                },
                {
                    "id": "r1-rating",
                    "component": {
                        "Text": {
                            "text": {"literalString": "Rating: ★★★★☆"}
                        }
                    }
                },
                {
                    "id": "r1-address",
                    "component": {
                        "Text": {
                            "usageHint": "caption",
                            "text": {"literalString": "81 St Marks Pl, New York"}
                        }
                    }
                },
                # Restaurant 2 Card
                {
                    "id": "restaurant2",
                    "component": {
                        "Card": {
                            "children": {"explicitList": ["r2-name", "r2-detail", "r2-info"]}
                        }
                    }
                },
                {
                    "id": "r2-name",
                    "component": {
                        "Text": {
                            "usageHint": "h2",
                            "text": {"literalString": "Han Dynasty"}
                        }
                    }
                },
                {
                    "id": "r2-detail",
                    "component": {
                        "Text": {
                            "text": {"literalString": "Authentic Szechuan cuisine."}
                        }
                    }
                },
                {
                    "id": "r2-info",
                    "component": {
                        "Row": {
                            "children": {"explicitList": ["r2-rating", "r2-address"]}
                        }
                    }
                },
                {
                    "id": "r2-rating",
                    "component": {
                        "Text": {
                            "text": {"literalString": "Rating: ★★★★☆"}
                        }
                    }
                },
                {
                    "id": "r2-address",
                    "component": {
                        "Text": {
                            "usageHint": "caption",
                            "text": {"literalString": "90 3rd Ave, New York"}
                        }
                    }
                },
            ]
        }
    })

    surface = renderer.get_surface("default")
    return A2UIComponent(surface)


def main():
    """Run the standalone A2UI demo."""
    print("Creating A2UI restaurant finder demo...")
    component = create_restaurant_ui()
    print("Launching Castella UI...")
    App(Frame("A2UI Demo - Restaurant Finder", 600, 500), component).run()


if __name__ == "__main__":
    main()
