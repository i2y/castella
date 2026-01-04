# A2UI Component Reference

Complete reference for all 17 A2UI components supported by Castella.

## Text Components

### Text

Display text content with optional styling.

```python
{
    "id": "title",
    "component": "Text",
    "text": {"literalString": "Hello, World!"},
    "usageHint": "h1"  # Optional: h1, h2, h3, h4, h5, body, caption
}
```

**Properties:**
- `text` - String value (literal or binding)
- `usageHint` - Styling hint: h1-h5 (headings), body, caption

### Icon

Display icon (Material Icons mapped to emoji).

```python
{
    "id": "icon1",
    "component": "Icon",
    "name": {"literalString": "home"}
}
```

**Icon mappings:**
- `home` → 🏠
- `search` → 🔍
- `settings` → ⚙️
- `person` → 👤
- `email` → 📧
- `phone` → 📱
- `star` → ⭐
- `check` → ✓
- `close` → ✕
- `arrow_back` → ←
- `arrow_forward` → →

### Markdown

Rich markdown rendering (Castella extension).

```python
{
    "id": "content",
    "component": "Markdown",
    "text": {"literalString": "# Title\n\n**Bold** text"}
}
```

## Input Components

### TextField

Single or multi-line text input.

```python
# Single line
{
    "id": "name_input",
    "component": "TextField",
    "text": {"path": "/name"},
    "usageHint": "text"
}

# Password (masked)
{
    "id": "password",
    "component": "TextField",
    "text": {"path": "/password"},
    "usageHint": "password"
}

# Multiline
{
    "id": "comments",
    "component": "TextField",
    "text": {"path": "/comments"},
    "usageHint": "multiline"
}
```

**usageHint values:**
- `text` (default) - Single line
- `password` / `obscured` - Masked input
- `multiline` - Multi-line editor

### CheckBox

Toggle checkbox.

```python
{
    "id": "agree",
    "component": "CheckBox",
    "checked": {"path": "/agreed"},
    "label": {"literalString": "I agree to the terms"}
}
```

### Slider

Range slider.

```python
{
    "id": "volume",
    "component": "Slider",
    "value": {"path": "/volume"},
    "min": {"literalNumber": 0},
    "max": {"literalNumber": 100}
}
```

### DateTimeInput

Date and/or time picker.

```python
{
    "id": "appointment",
    "component": "DateTimeInput",
    "value": {"path": "/datetime"},
    "enableDate": True,
    "enableTime": True
}
```

### ChoicePicker

Single or multiple selection from options.

```python
# Single selection (RadioButtons)
{
    "id": "size",
    "component": "ChoicePicker",
    "choices": [
        {"literalString": "Small"},
        {"literalString": "Medium"},
        {"literalString": "Large"}
    ],
    "selected": {"literalString": "Medium"},
    "allowMultiple": False
}

# Multiple selection (CheckBox list)
{
    "id": "toppings",
    "component": "ChoicePicker",
    "choices": [
        {"literalString": "Cheese"},
        {"literalString": "Pepperoni"},
        {"literalString": "Mushrooms"}
    ],
    "selected": {"path": "/selectedToppings"},
    "allowMultiple": True
}
```

## Button Component

### Button

Clickable button with action.

```python
{
    "id": "submit_btn",
    "component": "Button",
    "text": {"literalString": "Submit"},
    "action": {
        "name": "submit",
        "context": ["/formData"]
    }
}
```

**Properties:**
- `text` - Button label
- `action` - Action definition
  - `name` - Action identifier
  - `context` - Array of data paths to include

## Layout Components

### Row

Horizontal layout.

```python
{
    "id": "row1",
    "component": "Row",
    "children": {"explicitList": ["child1", "child2", "child3"]}
}
```

### Column

Vertical layout.

```python
{
    "id": "col1",
    "component": "Column",
    "children": {"explicitList": ["child1", "child2"]}
}
```

### Card

Container with visual styling.

```python
{
    "id": "card1",
    "component": "Card",
    "children": {"explicitList": ["content"]},
    "title": {"literalString": "Card Title"}
}
```

### Divider

Visual separator.

```python
{
    "id": "divider1",
    "component": "Divider",
    "orientation": "horizontal"  # or "vertical"
}
```

## List Component

### List

Dynamic list with template children.

```python
{
    "id": "user_list",
    "component": "List",
    "children": {
        "path": "/users",           # Data array path
        "componentId": "user_item"  # Template component ID
    }
}

# Template component (relative paths)
{
    "id": "user_item",
    "component": "Row",
    "children": {"explicitList": ["user_name", "user_email"]}
}
{
    "id": "user_name",
    "component": "Text",
    "text": {"path": "name"}  # Relative to list item
}
{
    "id": "user_email",
    "component": "Text",
    "text": {"path": "email"}
}
```

**Initial data:**
```python
{
    "/users": [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"}
    ]
}
```

## Navigation Components

### Tabs

Tabbed navigation.

```python
{
    "id": "tabs1",
    "component": "Tabs",
    "tabs": [
        {"id": "home", "label": {"literalString": "Home"}, "content": "home_content"},
        {"id": "settings", "label": {"literalString": "Settings"}, "content": "settings_content"}
    ],
    "selected": {"literalString": "home"}
}
```

### Modal

Overlay dialog.

```python
{
    "id": "modal1",
    "component": "Modal",
    "title": {"literalString": "Confirm"},
    "content": {"explicitList": ["modal_content"]},
    "open": {"path": "/modalOpen"}
}
```

## Media Components

### Image

Display image from URL.

```python
{
    "id": "photo",
    "component": "Image",
    "src": {"literalString": "https://example.com/image.png"},
    "alt": {"literalString": "Photo description"}
}
```

## Value Types Summary

### Literal Values

```python
{"literalString": "text"}     # String
{"literalNumber": 42}         # Number
{"literalBoolean": True}      # Boolean
```

### Data Binding

```python
{"path": "/absolute/path"}    # Absolute JSON Pointer
{"path": "relative/path"}     # Relative (in List templates)
```

### Children

```python
{"explicitList": ["id1", "id2"]}  # Static children

{"path": "/items", "componentId": "template"}  # TemplateChildren
```
