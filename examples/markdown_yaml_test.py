"""Test Markdown code block rendering with various languages."""

from castella import App, Column, Markdown
from castella.core import SizePolicy
from castella.frame import Frame

MARKDOWN_CONTENT = """
# Markdown Code Block Test

## YAML (previously crashed)

```yaml
name: castella
version: 0.13.8
dependencies:
  - pygments
  - markdown-it-py
```

## Python

```python
def hello():
    print("Hello, World!")

class MyClass:
    def __init__(self):
        self.value = 42
```

## JSON

```json
{
  "name": "castella",
  "version": "0.13.8",
  "features": ["markdown", "charts", "tables"]
}
```

## No language specified

```
This is plain text without syntax highlighting.
It should still render correctly.
```

## Inline code

You can also use `inline code` in markdown.
"""


def main():
    frame = Frame("Markdown YAML Test", 800, 600)
    content = Column(
        Markdown(MARKDOWN_CONTENT, base_font_size=14),
        scrollable=True,
    ).width_policy(SizePolicy.EXPANDING).height_policy(SizePolicy.EXPANDING)

    app = App(frame, content)
    app.run()


if __name__ == "__main__":
    main()
