# Hello World

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


## Example 1
Here you will create a UI that just displays "Hello World!".
For that, you need to use App, Frame and Text.

- App: Class that has the execution loop of an application
- Frame: Class representing the frame of the application window
- Text: Single-line text widget


The code is as follows.

```python
from castella import App, Text
from castella.frame import Frame

App(Frame("Hello world", 480, 300),　  # (1)
    Text("Hello World!")).run()　  # (2)
```

1.  Set the title of the Frame=Window of this app to "Hello world" and the size to 480 wide and 300 high.
2.  Initialize App by passing a Frame instance and a top-level widget (in this case, Text) to App constructor as a top-level widget, then call the run method; to run the App, you must finally call run after setting up the screen and event handlers.

You will see a screen similar to the one below with executing this.

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/hello_world.html"></iframe>
</div>

This is an screen shot of the result of running the above in dark mode.

In Castella, each widgets are automatically scaled to fit the size of the parent (in this case, the frame) by default.
Also, actual text inside of Text widget is rendered scaled to fit the size of the Text widget by default and is aligned to the center by default.


## Example 2

This is an example of fixing the font size to a specified size, regardless of the size of the Text widget and Frame.


```python
App(Frame("Hello world", 480, 300),
    Text("Hello World!", font_size=20)).run()
```
<div class="demo">
    <iframe width="100%" height="100%" src="../examples/hello_world_2.html"></iframe>
</div>

In addition, here is an example that the alignment of the actual text is left side.
You can specify that with `align=TextAlign.LEFT`.

```python
App(Frame("Hello world", 480, 300),
    Text("Hello World!", font_size=20, align=TextAlign.LEFT)).run()
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/hello_world_2_left.html"></iframe>
</div>

`TextAlign.RIGHT` can also be specified.


## Example 3
This example makes a text widget itself a fixed size.

```python
App(Frame("Hello world", 480, 300),
    Text("Hello World!").fixed_size(100, 200)).run()
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/hello_world_3.html"></iframe>
</div>

---

The next chapter describes Layout.
