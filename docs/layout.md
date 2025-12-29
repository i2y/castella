## Container Widget
Castella has three container widgets for UI layout; Column, Row and Box.

<style type="text/css">
    div.demo {
        margin: 8px;
        border: solid 1px #ccc;
        resize: both;
        overflow: hidden;
        width: 300px;
        height: 300px;
    }
</style>

### Column
Column aligns child elements vertically like this and the code looks like this.

```python
Column(
  Text("First", font_size=24),
  Text("Second", font_size=24),
  Text("Third", font_size=24),
)
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/column.html"></iframe>
</div>

### Row
Row aligns child elements horizontally like this and the code is this.

```python
Row(
  Text("First", font_size=24),
  Text("Second", font_size=24),
  Text("Third", font_size=24),
)
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/row.html"></iframe>
</div>

### Box
Box can take one or more children. All children are stacked at the same position, rendered in z-index order (lower first, higher on top). This enables creating overlays, modals, and layered UIs.

If a child's size is bigger than the parent box, the parent box provides scrollbars automatically.
(By the way, if you set scrollable=True for Column or Row, a scrollbar will appear when the child elements do not fit within the view.)

```python
# Simple scrollable content
Box(
  Text("Content", font_size=24).fixed_size(400, 400),
)

# Overlapping widgets with z-index
Box(
  Column(...).z_index(1),   # Background content
  Column(...).z_index(10),  # Modal on top
)
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/box.html"></iframe>
</div>

## Size Policy

Each widget has size policies for each width and height.
There are three types of policies that can be specified.

- Expanding: maximum size that will fit in the parent widget
- Fixed Size: specified size
- Content: size according to the content (e.g., for text, according to the size of that text)

The default policy is different depending on the kind of widget, but it is basically “Expanding” for both width and height.

For example, in the Row example above, the width policy of each Text widget is “Expanding" and the height policy is "Expanding”.


```python
Row(
  Text("First", font_size=24),
  Text("Second", font_size=24),
  Text("Third", font_size=24),
)
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/row.html"></iframe>
</div>

In this case, the width of each Text widget is expanded to the width of the parent Row widget and share their width equally, and the height of each Text widget is expanded to the height of the parent Row widget.

The code above is same with the code below written without omission of the size policy setting.

```python
Row(
  Text("First", font_size=24).WidthPolicy(SizePolicy.Expanding)
                             .HeightPolicy(SizePolicy.Expanding),
  Text("Second", font_size=24).WidthPolicy(SizePolicy.Expanding)
                              .HeightPolicy(SizePolicy.Expanding),
  Text("Third", font_size=24).WidthPolicy(SizePolicy.Expanding)
                             .HeightPolicy(SizePolicy.Expanding),
)
```

### Flex
By specifying "flex" you can specify each widget's occupied ratio for the overall size in the parent widget.

```python
Row(
  Text("First", font_size=24).flex(1),
  Text("Second", font_size=24).flex(2),
  Text("Third", font_size=24).flex(1),
)
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/row_with_flex.html"></iframe>
</div>

In this example above, the width of the entire row is divided in the ratio 1:2:1.


### Mix of various size policies
Of course, you can mix multiple size policies for the children of a single parent widget.

```python
Row(
  Text("First", font_size=24).fixed_size(100, 50),
  Text("Second", font_size=24).flex(2),
  Text("Third", font_size=24).flex(1),
)
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/row_with_fixed_and_flex.html"></iframe>
</div>

In this example, the first element is displayed at the specified fixed size. The remaining two child elements share the remaining width in 2:1 ratio.

## Z-Index (Stacking Order)

Widgets can be layered using the `z_index()` method. Higher values appear on top and receive input events first.

```python
main_content = Column(...).z_index(1)
modal = Column(...).z_index(10)  # Appears on top
return Box(main_content, modal)
```

For detailed information and examples, see [Z-Index and Layering](z-index.md).
