"""Demo of extended Markdown syntax features.

This example demonstrates all the new Markdown extensions:
- GitHub-style Admonitions
- Definition Lists
- Emoji Shortcodes
- Table of Contents
- Mermaid Diagrams (Flowchart, Sequence, State, Class)

Run with: uv run python examples/markdown_extended_demo.py
"""

from castella import App, Column, Markdown, ScrollState, SizePolicy
from castella.frame import Frame

MARKDOWN_CONTENT = """
# Markdown Extended Syntax Demo

[TOC]

## GitHub-style Admonitions

GitHub-flavored admonitions provide highlighted callout blocks.

> [!NOTE]
> This is a note. Use it for additional information.

> [!TIP]
> This is a tip. Use it for helpful suggestions.

> [!IMPORTANT]
> This is important information that users should pay attention to.

> [!WARNING]
> This is a warning. Use it to alert users about potential issues.

> [!CAUTION]
> This is a caution. Use it for serious warnings.

## Definition Lists

HTML Term
:   A markup language used for structuring web content.
:   Can have multiple definitions.

CSS Term
:   Cascading Style Sheets for styling HTML documents.

JavaScript
:   A programming language for web interactivity.

## Task Lists (TODO)

Track progress with checkboxes:

- [x] Implement Markdown parser
- [x] Add syntax highlighting
- [x] Support Mermaid diagrams
- [ ] Add more diagram types
- [ ] Write documentation

## Emoji Shortcodes

Emoji shortcodes are converted to Unicode characters:

- :smile: Happy face
- :heart: Love and affection
- :rocket: Launch and speed
- :star: Excellence
- :fire: Hot topics
- :thumbsup: Approval
- :bulb: Ideas
- :warning: Caution
- :check: Success
- :x: Failure

## Mermaid Diagrams

### Flowchart

```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E
```

### Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant Database
    Client->>Server: Request
    Server->>Database: Query
    Database-->>Server: Results
    Server-->>Client: Response
```

### State Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Running: start
    Running --> Paused: pause
    Paused --> Running: resume
    Running --> Idle: stop
    Running --> [*]: terminate
```

### Class Diagram

```mermaid
classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    class Dog {
        +String breed
        +bark()
    }
    class Cat {
        +meow()
    }
    Animal <|-- Dog
    Animal <|-- Cat
```

## Standard Markdown Features

These are still supported alongside the new extensions.

### Text Formatting

**Bold text** and *italic text* and ~~strikethrough~~.

### Code Blocks

```python
def hello_world():
    print("Hello, Markdown!")

class Example:
    def __init__(self):
        self.value = 42
```

### Tables

| Feature | Status | Notes |
|---------|--------|-------|
| Admonitions | :check: | GitHub-style |
| Definition Lists | :check: | Standard syntax |
| Emoji | :check: | Shortcodes |
| Mermaid | :check: | Pure Python |

### Lists

1. First item
2. Second item
   - Nested bullet
   - Another nested
3. Third item

### Blockquotes

> This is a regular blockquote.
> It can span multiple lines.

### Links

External links open in your browser:
- [GitHub](https://github.com)
- [Python.org](https://python.org)

Internal links (TOC entries above) scroll to the heading.

### Math (LaTeX)

Inline math: $E = mc^2$

Block math:
$$
\\frac{n!}{k!(n-k)!} = \\binom{n}{k}
$$

---

*End of demo*
"""


def main():
    frame = Frame(
        "Markdown Extended Syntax Demo",
        width=900,
        height=700,
    )

    # Create ScrollState for TOC navigation
    scroll_state = ScrollState()

    # Create scrollable Markdown view with all extensions enabled
    # Pass scroll_state to enable TOC link navigation
    markdown = (
        Markdown(
            MARKDOWN_CONTENT,
            base_font_size=14,
            enable_admonitions=True,
            enable_mermaid=True,
            enable_deflist=True,
            enable_toc=True,
            scroll_state=scroll_state,  # Enable TOC navigation
        )
        .width_policy(SizePolicy.EXPANDING)
        .height_policy(SizePolicy.CONTENT)
    )

    content = Column(
        markdown,
        scrollable=True,
        scroll_state=scroll_state,  # Share scroll state with Column
    ).width_policy(SizePolicy.EXPANDING).height_policy(SizePolicy.EXPANDING)

    App(frame, content).run()


if __name__ == "__main__":
    main()
