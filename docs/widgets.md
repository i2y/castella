## Button
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

```python
App(
    Frame("Button"),
    Row(
        Column(
            Button("First"),
            Button("Second", align=TextAlign.CENTER),
            Button("Third", align=TextAlign.RIGHT),
            Button("Fourth", align=TextAlign.LEFT),
        ).spacing(10)
    ).spacing(10),
).run()
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/button.html"></iframe>
</div>


## Text

```python
App(
    Frame("Button"),
    Row(
        Column(
            Text("First", kind=Kind.NORMAL),
            Text("Second", kind=Kind.INFO, align=TextAlign.CENTER),
            Text("Third", kind=Kind.SUCCESS, align=TextAlign.RIGHT),
            Text("Fourth", kind=Kind.WARNING, align=TextAlign.LEFT),
            Text("Fifth", kind=Kind.DANGER, align=TextAlign.LEFT),
        ).spacing(10)
    ).spacing(10),
).run()

```


<div class="demo">
    <iframe width="100%" height="100%" src="../examples/text.html"></iframe>
</div>

## Switch

```python
App(
    Frame("Switch"),
    Switch(True),
).run()
```

<div class="demo" style="width: 100px; height: 50px">
    <iframe width="100%" height="100%" src="../examples/switch.html"></iframe>
</div>

## And more...
This document is WIP. In the future, we will add explanation for more widgets and examples in this document.
For now, please see the ["examples" directory](https://github.com/i2y/castella/tree/main/examples) for more widgets and the examples.
