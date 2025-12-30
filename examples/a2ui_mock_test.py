"""A2UI Mock Data Tests - Tests A2UI renderer with simulated agent responses.

This file contains mock data that simulates responses from Google's A2UI
sample agents, allowing testing without actual API calls.

Run with:
    uv run python examples/a2ui_mock_test.py [test_name]

Available tests:
    restaurant  - Restaurant list with images and buttons
    form        - Booking form with TextField, DateTimeInput, etc.
    all         - Run all tests sequentially
"""

from castella import App
from castella.a2ui import A2UIRenderer, A2UIComponent, UserAction
from castella.frame import Frame


def create_action_handler():
    """Create a default action handler that prints actions."""
    def on_action(action: UserAction):
        print(f"Action: {action.name} from {action.source_component_id}")
        print(f"  Context: {action.context}")
    return on_action


def test_restaurant_list():
    """Test restaurant list with images, buttons, and template children.

    Components tested:
    - Text (h1, h3, body)
    - Image (NetImage)
    - Button (with action)
    - Row/Column layout
    - Card container
    - List with TemplateChildren
    """
    renderer = A2UIRenderer()
    renderer._on_action = create_action_handler()

    # beginRendering
    renderer.handle_message({
        'beginRendering': {
            'surfaceId': 'default',
            'root': 'root-column'
        }
    })

    # surfaceUpdate with components (legacy format matching Google's agents)
    renderer.handle_message({
        'surfaceUpdate': {
            'surfaceId': 'default',
            'components': [
                {
                    'id': 'root-column',
                    'component': {
                        'Column': {
                            'children': {'explicitList': ['title', 'restaurant-list']}
                        }
                    }
                },
                {
                    'id': 'title',
                    'component': {
                        'Text': {
                            'usageHint': 'h1',
                            'text': {'literalString': 'Top Restaurants'}
                        }
                    }
                },
                {
                    'id': 'restaurant-list',
                    'component': {
                        'List': {
                            'children': {
                                'template': {
                                    'componentId': 'item-card',
                                    'dataBinding': '/items'
                                }
                            }
                        }
                    }
                },
                # Card with Row layout (image + details side by side)
                {
                    'id': 'item-card',
                    'component': {
                        'Card': {
                            'children': {'explicitList': ['card-row']}
                        }
                    }
                },
                {
                    'id': 'card-row',
                    'component': {
                        'Row': {
                            'children': {'explicitList': ['card-image', 'card-details']}
                        }
                    }
                },
                {
                    'id': 'card-image',
                    'weight': 1,
                    'component': {
                        'Image': {
                            'url': {'path': 'imageUrl'}
                        }
                    }
                },
                {
                    'id': 'card-details',
                    'weight': 2,
                    'component': {
                        'Column': {
                            'children': {'explicitList': [
                                'item-name', 'item-rating', 'item-detail', 'item-button'
                            ]}
                        }
                    }
                },
                {
                    'id': 'item-name',
                    'component': {
                        'Text': {
                            'usageHint': 'h3',
                            'text': {'path': 'name'}
                        }
                    }
                },
                {
                    'id': 'item-rating',
                    'component': {
                        'Text': {
                            'text': {'path': 'rating'}
                        }
                    }
                },
                {
                    'id': 'item-detail',
                    'component': {
                        'Text': {
                            'text': {'path': 'detail'}
                        }
                    }
                },
                {
                    'id': 'item-button',
                    'component': {
                        'Button': {
                            'text': {'literalString': 'Book Now'},
                            'action': {
                                'name': 'book_restaurant',
                                'context': [
                                    {'key': 'restaurantName', 'value': {'path': 'name'}}
                                ]
                            }
                        }
                    }
                }
            ]
        }
    })

    # dataModelUpdate with restaurant data (legacy format)
    renderer.handle_message({
        'dataModelUpdate': {
            'surfaceId': 'default',
            'path': '/',
            'contents': [
                {
                    'key': 'items',
                    'valueList': [
                        {
                            'valueMap': [
                                {'key': 'name', 'valueString': "Xi'an Famous Foods"},
                                {'key': 'rating', 'valueString': '****'},  # Avoid Unicode stars
                                {'key': 'detail', 'valueString': 'Spicy hand-pulled noodles'},
                                {'key': 'imageUrl', 'valueString': 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=200'}
                            ]
                        },
                        {
                            'valueMap': [
                                {'key': 'name', 'valueString': 'Han Dynasty'},
                                {'key': 'rating', 'valueString': '****'},
                                {'key': 'detail', 'valueString': 'Authentic Szechuan cuisine'},
                                {'key': 'imageUrl', 'valueString': 'https://images.unsplash.com/photo-1563245372-f21724e3856d?w=200'}
                            ]
                        }
                    ]
                }
            ]
        }
    })

    surface = renderer.get_surface('default')
    print("Restaurant List Test")
    print("=" * 40)
    print("Components: Text, Image, Button, Row, Column, Card, List")
    print("Click 'Book Now' to test action handling")
    print()

    App(Frame('A2UI Restaurant List', 700, 600), A2UIComponent(surface)).run()


def test_booking_form():
    """Test booking form with input components.

    Components tested:
    - TextField (shortText, number)
    - DateTimeInput
    - CheckBox
    - Slider
    - Divider
    - Button
    """
    renderer = A2UIRenderer()
    renderer._on_action = create_action_handler()

    renderer.handle_message({
        'beginRendering': {
            'surfaceId': 'default',
            'root': 'root'
        }
    })

    renderer.handle_message({
        'surfaceUpdate': {
            'surfaceId': 'default',
            'components': [
                {
                    'id': 'root',
                    'component': {
                        'Column': {
                            'children': {'explicitList': [
                                'title', 'divider1',
                                'name-field', 'party-size',
                                'divider2',
                                'datetime-field',
                                'divider3',
                                'checkbox-field',
                                'slider-field',
                                'submit-btn'
                            ]}
                        }
                    }
                },
                {
                    'id': 'title',
                    'component': {
                        'Text': {
                            'usageHint': 'h2',
                            'text': {'literalString': 'Booking Form'}
                        }
                    }
                },
                {'id': 'divider1', 'component': {'Divider': {}}},
                {
                    'id': 'name-field',
                    'component': {
                        'TextField': {
                            'label': {'literalString': 'Your Name'},
                            'text': {'path': '/name'},
                            'usageHint': 'shortText'
                        }
                    }
                },
                {
                    'id': 'party-size',
                    'component': {
                        'TextField': {
                            'label': {'literalString': 'Party Size'},
                            'text': {'path': '/partySize'},
                            'usageHint': 'number'
                        }
                    }
                },
                {'id': 'divider2', 'component': {'Divider': {}}},
                {
                    'id': 'datetime-field',
                    'component': {
                        'DateTimeInput': {
                            'label': {'literalString': 'Date & Time'},
                            'value': {'path': '/reservationTime'},
                            'enableDate': True,
                            'enableTime': True
                        }
                    }
                },
                {'id': 'divider3', 'component': {'Divider': {}}},
                {
                    'id': 'checkbox-field',
                    'component': {
                        'CheckBox': {
                            'label': {'literalString': 'Outdoor seating'},
                            'checked': {'path': '/outdoor'}
                        }
                    }
                },
                {
                    'id': 'slider-field',
                    'component': {
                        'Slider': {
                            'value': {'path': '/budget'},
                            'min': 0,
                            'max': 100
                        }
                    }
                },
                {
                    'id': 'submit-btn',
                    'component': {
                        'Button': {
                            'text': {'literalString': 'Submit Booking'},
                            'action': {
                                'name': 'submit_booking',
                                'context': []
                            }
                        }
                    }
                }
            ]
        }
    })

    renderer.handle_message({
        'dataModelUpdate': {
            'surfaceId': 'default',
            'path': '/',
            'contents': [
                {'key': 'name', 'valueString': 'John Doe'},
                {'key': 'partySize', 'valueString': '2'},
                {'key': 'reservationTime', 'valueString': '2024-12-31T19:00'},
                {'key': 'outdoor', 'valueBoolean': False},
                {'key': 'budget', 'valueNumber': 50}
            ]
        }
    })

    surface = renderer.get_surface('default')
    print("Booking Form Test")
    print("=" * 40)
    print("Components: TextField, DateTimeInput, CheckBox, Slider, Divider, Button")
    print()

    App(Frame('A2UI Booking Form', 500, 600), A2UIComponent(surface)).run()


def test_simple_text():
    """Simple test with just text components.

    Components tested:
    - Text with various usageHint values (h1-h5, body, caption)
    """
    renderer = A2UIRenderer()

    renderer.handle_message({
        'beginRendering': {
            'surfaceId': 'default',
            'root': 'root'
        }
    })

    renderer.handle_message({
        'surfaceUpdate': {
            'surfaceId': 'default',
            'components': [
                {
                    'id': 'root',
                    'component': {
                        'Column': {
                            'children': {'explicitList': [
                                'h1', 'h2', 'h3', 'h4', 'h5', 'body', 'caption'
                            ]}
                        }
                    }
                },
                {'id': 'h1', 'component': {'Text': {'usageHint': 'h1', 'text': {'literalString': 'Heading 1 (32px)'}}}},
                {'id': 'h2', 'component': {'Text': {'usageHint': 'h2', 'text': {'literalString': 'Heading 2 (28px)'}}}},
                {'id': 'h3', 'component': {'Text': {'usageHint': 'h3', 'text': {'literalString': 'Heading 3 (24px)'}}}},
                {'id': 'h4', 'component': {'Text': {'usageHint': 'h4', 'text': {'literalString': 'Heading 4 (20px)'}}}},
                {'id': 'h5', 'component': {'Text': {'usageHint': 'h5', 'text': {'literalString': 'Heading 5 (18px)'}}}},
                {'id': 'body', 'component': {'Text': {'usageHint': 'body', 'text': {'literalString': 'Body text (14px)'}}}},
                {'id': 'caption', 'component': {'Text': {'usageHint': 'caption', 'text': {'literalString': 'Caption text (12px)'}}}}
            ]
        }
    })

    surface = renderer.get_surface('default')
    print("Text Styles Test")
    print("=" * 40)
    print("Testing Text component with various usageHint values")
    print()

    App(Frame('A2UI Text Styles', 400, 400), A2UIComponent(surface)).run()


def test_tabs():
    """Test Tabs component.

    Components tested:
    - Tabs with multiple tab items
    - Tab switching
    """
    renderer = A2UIRenderer()
    renderer._on_action = create_action_handler()

    renderer.handle_message({
        'beginRendering': {
            'surfaceId': 'default',
            'root': 'root'
        }
    })

    renderer.handle_message({
        'surfaceUpdate': {
            'surfaceId': 'default',
            'components': [
                {
                    'id': 'root',
                    'component': {
                        'Column': {
                            'children': {'explicitList': ['title', 'tabs-widget']}
                        }
                    }
                },
                {
                    'id': 'title',
                    'component': {
                        'Text': {
                            'usageHint': 'h2',
                            'text': {'literalString': 'Tabs Demo'}
                        }
                    }
                },
                {
                    'id': 'tabs-widget',
                    'component': {
                        'Tabs': {
                            'tabItems': [
                                {'id': 'tab1', 'label': {'literalString': 'Overview'}, 'contentId': 'tab1-content'},
                                {'id': 'tab2', 'label': {'literalString': 'Details'}, 'contentId': 'tab2-content'},
                                {'id': 'tab3', 'label': {'literalString': 'Reviews'}, 'contentId': 'tab3-content'}
                            ],
                            'selectedTab': {'literalString': 'tab1'}
                        }
                    }
                },
                {
                    'id': 'tab1-content',
                    'component': {
                        'Text': {
                            'text': {'literalString': 'This is the Overview tab content.'}
                        }
                    }
                },
                {
                    'id': 'tab2-content',
                    'component': {
                        'Text': {
                            'text': {'literalString': 'This is the Details tab content.'}
                        }
                    }
                },
                {
                    'id': 'tab3-content',
                    'component': {
                        'Text': {
                            'text': {'literalString': 'This is the Reviews tab content.'}
                        }
                    }
                }
            ]
        }
    })

    surface = renderer.get_surface('default')
    print("Tabs Test")
    print("=" * 40)
    print("Components: Tabs with 3 tabs")
    print("Click tabs to switch between them")
    print()

    App(Frame('A2UI Tabs', 500, 400), A2UIComponent(surface)).run()


def test_choice_picker():
    """Test ChoicePicker component (RadioButtons).

    Components tested:
    - ChoicePicker with single selection
    - ChoicePicker with multiple selection
    """
    renderer = A2UIRenderer()
    renderer._on_action = create_action_handler()

    renderer.handle_message({
        'beginRendering': {
            'surfaceId': 'default',
            'root': 'root'
        }
    })

    renderer.handle_message({
        'surfaceUpdate': {
            'surfaceId': 'default',
            'components': [
                {
                    'id': 'root',
                    'component': {
                        'Column': {
                            'children': {'explicitList': [
                                'title',
                                'single-label', 'single-picker',
                                'multi-label', 'multi-picker',
                                'submit-btn'
                            ]}
                        }
                    }
                },
                {
                    'id': 'title',
                    'component': {
                        'Text': {
                            'usageHint': 'h2',
                            'text': {'literalString': 'ChoicePicker Demo'}
                        }
                    }
                },
                {
                    'id': 'single-label',
                    'component': {
                        'Text': {
                            'usageHint': 'h4',
                            'text': {'literalString': 'Select your cuisine (single):'}
                        }
                    }
                },
                {
                    'id': 'single-picker',
                    'component': {
                        'ChoicePicker': {
                            'choices': [
                                {'literalString': 'Chinese'},
                                {'literalString': 'Japanese'},
                                {'literalString': 'Italian'},
                                {'literalString': 'Mexican'}
                            ],
                            'selected': {'literalString': 'Chinese'},
                            'allowMultiple': False
                        }
                    }
                },
                {
                    'id': 'multi-label',
                    'component': {
                        'Text': {
                            'usageHint': 'h4',
                            'text': {'literalString': 'Select dietary restrictions (multiple):'}
                        }
                    }
                },
                {
                    'id': 'multi-picker',
                    'component': {
                        'ChoicePicker': {
                            'choices': [
                                {'literalString': 'Vegetarian'},
                                {'literalString': 'Vegan'},
                                {'literalString': 'Gluten-free'},
                                {'literalString': 'Nut-free'}
                            ],
                            'selected': {'path': '/dietary'},
                            'allowMultiple': True
                        }
                    }
                },
                {
                    'id': 'submit-btn',
                    'component': {
                        'Button': {
                            'text': {'literalString': 'Submit'},
                            'action': {'name': 'submit', 'context': []}
                        }
                    }
                }
            ]
        }
    })

    renderer.handle_message({
        'dataModelUpdate': {
            'surfaceId': 'default',
            'path': '/',
            'contents': [
                {'key': 'dietary', 'valueList': []}
            ]
        }
    })

    surface = renderer.get_surface('default')
    print("ChoicePicker Test")
    print("=" * 40)
    print("Components: ChoicePicker (single and multiple selection)")
    print()

    App(Frame('A2UI ChoicePicker', 400, 500), A2UIComponent(surface)).run()


def test_icon():
    """Test Icon component.

    Components tested:
    - Icon with various material icon names
    - Icon mapped to emoji/symbols
    """
    renderer = A2UIRenderer()

    renderer.handle_message({
        'beginRendering': {
            'surfaceId': 'default',
            'root': 'root'
        }
    })

    renderer.handle_message({
        'surfaceUpdate': {
            'surfaceId': 'default',
            'components': [
                {
                    'id': 'root',
                    'component': {
                        'Column': {
                            'children': {'explicitList': [
                                'title', 'row1', 'row2', 'row3', 'row4'
                            ]}
                        }
                    }
                },
                {
                    'id': 'title',
                    'component': {
                        'Text': {
                            'usageHint': 'h2',
                            'text': {'literalString': 'Icon Demo'}
                        }
                    }
                },
                {
                    'id': 'row1',
                    'component': {
                        'Row': {'children': {'explicitList': ['icon1', 'label1']}}
                    }
                },
                {'id': 'icon1', 'component': {'Icon': {'name': {'literalString': 'calendar_today'}}}},
                {'id': 'label1', 'component': {'Text': {'text': {'literalString': 'Calendar'}}}},
                {
                    'id': 'row2',
                    'component': {
                        'Row': {'children': {'explicitList': ['icon2', 'label2']}}
                    }
                },
                {'id': 'icon2', 'component': {'Icon': {'name': {'literalString': 'location_on'}}}},
                {'id': 'label2', 'component': {'Text': {'text': {'literalString': 'Location'}}}},
                {
                    'id': 'row3',
                    'component': {
                        'Row': {'children': {'explicitList': ['icon3', 'label3']}}
                    }
                },
                {'id': 'icon3', 'component': {'Icon': {'name': {'literalString': 'mail'}}}},
                {'id': 'label3', 'component': {'Text': {'text': {'literalString': 'Email'}}}},
                {
                    'id': 'row4',
                    'component': {
                        'Row': {'children': {'explicitList': ['icon4', 'label4']}}
                    }
                },
                {'id': 'icon4', 'component': {'Icon': {'name': {'literalString': 'call'}}}},
                {'id': 'label4', 'component': {'Text': {'text': {'literalString': 'Phone'}}}},
            ]
        }
    })

    surface = renderer.get_surface('default')
    print("Icon Test")
    print("=" * 40)
    print("Components: Icon (calendar, location, mail, call)")
    print()

    App(Frame('A2UI Icons', 400, 400), A2UIComponent(surface)).run()


def test_modal():
    """Test Modal component.

    Components tested:
    - Modal with open/close
    - Button to trigger modal
    """
    renderer = A2UIRenderer()
    renderer._on_action = create_action_handler()

    renderer.handle_message({
        'beginRendering': {
            'surfaceId': 'default',
            'root': 'root'
        }
    })

    renderer.handle_message({
        'surfaceUpdate': {
            'surfaceId': 'default',
            'components': [
                {
                    'id': 'root',
                    'component': {
                        'Column': {
                            'children': {'explicitList': ['title', 'info', 'open-btn', 'modal-widget']}
                        }
                    }
                },
                {
                    'id': 'title',
                    'component': {
                        'Text': {
                            'usageHint': 'h2',
                            'text': {'literalString': 'Modal Demo'}
                        }
                    }
                },
                {
                    'id': 'info',
                    'component': {
                        'Text': {
                            'text': {'literalString': 'Click the button below to open a modal dialog.'}
                        }
                    }
                },
                {
                    'id': 'open-btn',
                    'component': {
                        'Button': {
                            'text': {'literalString': 'Open Modal'},
                            'action': {'name': 'open_modal', 'context': []}
                        }
                    }
                },
                {
                    'id': 'modal-widget',
                    'component': {
                        'Modal': {
                            'title': {'literalString': 'Confirmation'},
                            'open': {'path': '/modalOpen'},
                            'children': {'explicitList': ['modal-content', 'modal-close-btn']}
                        }
                    }
                },
                {
                    'id': 'modal-content',
                    'component': {
                        'Text': {
                            'text': {'literalString': 'This is the modal content. Are you sure you want to proceed?'}
                        }
                    }
                },
                {
                    'id': 'modal-close-btn',
                    'component': {
                        'Button': {
                            'text': {'literalString': 'Close'},
                            'action': {'name': 'close_modal', 'context': []}
                        }
                    }
                }
            ]
        }
    })

    renderer.handle_message({
        'dataModelUpdate': {
            'surfaceId': 'default',
            'path': '/',
            'contents': [
                {'key': 'modalOpen', 'valueBoolean': False}
            ]
        }
    })

    surface = renderer.get_surface('default')
    print("Modal Test")
    print("=" * 40)
    print("Components: Modal with open/close buttons")
    print("Note: Modal state is controlled by data binding")
    print()

    App(Frame('A2UI Modal', 500, 400), A2UIComponent(surface)).run()


def print_usage():
    print(__doc__)


def main():
    import sys

    tests = {
        'restaurant': test_restaurant_list,
        'form': test_booking_form,
        'text': test_simple_text,
        'tabs': test_tabs,
        'choice': test_choice_picker,
        'icon': test_icon,
        'modal': test_modal,
    }

    if len(sys.argv) < 2:
        print_usage()
        print("\nAvailable tests:", ', '.join(tests.keys()))
        print("\nRunning 'restaurant' test by default...\n")
        test_restaurant_list()
        return

    test_name = sys.argv[1].lower()

    if test_name == 'all':
        for name, test_func in tests.items():
            print(f"\n{'=' * 50}")
            print(f"Running test: {name}")
            print('=' * 50)
            test_func()
    elif test_name in tests:
        tests[test_name]()
    else:
        print(f"Unknown test: {test_name}")
        print_usage()
        print("\nAvailable tests:", ', '.join(tests.keys()))


if __name__ == "__main__":
    main()
