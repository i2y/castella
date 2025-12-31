# Sizing

Castella widgets use a **SizePolicy** system to control how they size themselves within their parent container. This page explains the sizing system and the convenient syntax sugar methods available.

## SizePolicy

Every widget has independent width and height policies:

| Policy | Description |
|--------|-------------|
| `FIXED` | Widget uses the exact size specified |
| `EXPANDING` | Widget expands to fill available space |
| `CONTENT` | Widget sizes itself to fit its content |

### Default Policies

Most widgets default to `EXPANDING` for both dimensions, meaning they fill available space:

```python
# These two are equivalent
Text("Hello")
Text("Hello").width_policy(SizePolicy.EXPANDING).height_policy(SizePolicy.EXPANDING)
```

Some widgets like `Image` and `Markdown` default to `CONTENT` policy.

## Syntax Sugar Methods

Castella provides convenient methods that combine size and policy settings:

### Fixed Sizing

```python
# Set fixed width (100px)
widget.fixed_width(100)
# Equivalent to: widget.width(100).width_policy(SizePolicy.FIXED)

# Set fixed height (40px)
widget.fixed_height(40)
# Equivalent to: widget.height(40).height_policy(SizePolicy.FIXED)

# Set both dimensions at once
widget.fixed_size(200, 100)
# Equivalent to: widget.width(200).width_policy(SizePolicy.FIXED)
#                     .height(100).height_policy(SizePolicy.FIXED)
```

### Content Sizing

```python
# Size to content in both dimensions
widget.fit_content()
# Equivalent to: widget.width_policy(SizePolicy.CONTENT)
#                     .height_policy(SizePolicy.CONTENT)

# Size to content width only
widget.fit_content_width()
# Equivalent to: widget.width_policy(SizePolicy.CONTENT)

# Size to content height only
widget.fit_content_height()
# Equivalent to: widget.height_policy(SizePolicy.CONTENT)
```

### Parent Filling

```python
# Expand to fill parent in both dimensions
widget.fit_parent()
# Equivalent to: widget.width_policy(SizePolicy.EXPANDING)
#                     .height_policy(SizePolicy.EXPANDING)
```

## Practical Examples

### Fixed Height Row

```python
Row(
    Button("Save"),
    Button("Cancel"),
).fixed_height(50)
```

### Scrollable List with Fixed Item Heights

```python
Column(
    *[Text(item).fixed_height(30) for item in items],
    scrollable=True,
)
```

### Fixed Width Sidebar

```python
Row(
    Column(
        Text("Sidebar"),
        # sidebar content...
    ).fixed_width(200),
    Column(
        Text("Main Content"),
        # main content...
    ),  # Expands to fill remaining space
)
```

### Input with Fixed Height

```python
MultilineInput(state, font_size=14, wrap=True).fixed_height(200)
```

### Chart with Fixed Height

```python
Row(
    GaugeChart(data),
    Button("Update"),
).fixed_height(200)
```

## Comparison: Before and After

Using syntax sugar methods makes code more readable and concise:

=== "Before (verbose)"

    ```python
    from castella import Column, Text, Button, SizePolicy

    Column(
        Text("Title")
            .height(40)
            .height_policy(SizePolicy.FIXED),
        Text("Content"),
        Button("Submit")
            .width(100)
            .width_policy(SizePolicy.FIXED)
            .height(40)
            .height_policy(SizePolicy.FIXED),
    )
    ```

=== "After (syntax sugar)"

    ```python
    from castella import Column, Text, Button

    Column(
        Text("Title").fixed_height(40),
        Text("Content"),
        Button("Submit").fixed_size(100, 40),
    )
    ```

Benefits:
- No need to import `SizePolicy`
- Single method call instead of two
- Code is more readable and self-documenting

## CONTENT Policy Constraint

When using `CONTENT` height policy on a layout container, all children must also have `CONTENT` or `FIXED` height policy:

```python
# This will raise RuntimeError:
Column(
    Text("Hello"),  # Text defaults to EXPANDING height
).fit_content_height()

# Fix by setting children to FIXED:
Column(
    Text("Hello").fixed_height(24),
).fit_content_height()

# Or use widgets that default to CONTENT:
Column(
    Markdown("# Hello"),  # Markdown defaults to CONTENT
).fit_content_height()
```

## Method Reference

| Method | Description |
|--------|-------------|
| `fixed_width(w)` | Set fixed width |
| `fixed_height(h)` | Set fixed height |
| `fixed_size(w, h)` | Set fixed width and height |
| `fit_content()` | Size to content (both dimensions) |
| `fit_content_width()` | Size to content width |
| `fit_content_height()` | Size to content height |
| `fit_parent()` | Expand to fill parent (both dimensions) |
| `width(w)` | Set width value |
| `height(h)` | Set height value |
| `width_policy(p)` | Set width policy |
| `height_policy(p)` | Set height policy |
| `flex(n)` | Set flex ratio in layouts |
