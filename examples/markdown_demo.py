"""Demo for Markdown widget."""

from castella import App, Column, Markdown, SizePolicy
from castella.frame import Frame


DEMO_MARKDOWN = """
# Markdown Demo

This is a demonstration of the **Markdown** widget in Castella.

## Text Formatting

You can use **bold**, *italic*, and ~~strikethrough~~ text.
Combine them: ***bold italic*** or **bold with ~~strikethrough~~**.

## Lists

### Unordered List
- First item
- Second item
- Third item with **bold**

### Ordered List
1. Step one
2. Step two
3. Step three

### Task List
- [x] Completed task
- [ ] Pending task
- [x] Another done

## Code

Inline code: `print("Hello")`

Code block with syntax highlighting:

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Calculate first 10 numbers
for i in range(10):
    print(fibonacci(i))
```

## Tables

| Name | Language | Stars |
|------|----------|-------|
| Castella | Python | 100+ |
| React | JavaScript | 200k+ |
| Vue | JavaScript | 200k+ |

## Blockquotes

> This is a blockquote.
> It can span multiple lines.

## Math (LaTeX)

Inline math: $E = mc^2$

Block math:

```math
\\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}
```

## Links

Visit [Castella on GitHub](https://github.com/i2y/castella) for more info.

---

*End of demo*
"""


def on_link(href: str):
    print(f"Link clicked: {href}")


def main():
    app = App(
        Frame("Markdown Demo", width=800, height=600),
        Column(
            Markdown(DEMO_MARKDOWN, base_font_size=14, on_link_click=on_link)
            .width_policy(SizePolicy.EXPANDING)
            .height_policy(SizePolicy.EXPANDING),
        ),
    )
    app.run()


if __name__ == "__main__":
    main()
