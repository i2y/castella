You can combine built-in widgets to create a custom widget. It is defined as a subclass of Component or a subclass of Stateful Component. (You can also define custom widgets without combining existing widgets, but that's another story.)

## Component
Component is a custom widget that doesn’t have the state of the component as a whole.

This is an example code for counter component.

```python
class Counter(Component):
    def __init__(self):
        super().__init__()
        self._count = State(0)

    def view(self):
        return Column(
            Text(self._count),
            Row(
                Button("Up", font_size=50).on_click(self.up),
                Button("Down", font_size=50).on_click(self.down),
            ),
        )

    def up(self, _):
        self._count += 1

    def down(self, _):
        self._count -= 1
```

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

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/counter.html"></iframe>
</div>

This counter component has count state as an instance variable. However, it is bound only to the child text widget, not to the state of this component. Therefore, there is no need to even make it an instance variable if the encapsulation of the count state is unnecessary.

When this state is changed, only the child text widget is re-rendered, and the entire component is not re-rendered. On the other hand, a stateful component binds specific states to components. When that state changes, the entire component is re-rendered according to the content of the view method. If you need to re-render the entire component when something changes, you should use a StatefulComponent.

Here is an example of the counter app written without instance variables. Either way of writing is fine.

```python
class Counter(Component):
    def view(self):
        count = State(0)
        up = lambda _: count.set(count() + 1)
        down = lambda _: count.set(count() - 1)
        return Column(
            Text(count),
            Row(
                Button("+", font_size=50).on_click(up),
                Button("-", font_size=50).on_click(down),
            ),
        )
```


## Stateful Component
Stateful Component is a custom widget that has state as the component.

Here is an example of a numeric list component. This component is a stateful component.

```python
class NumList(StatefulComponent):
    def __init__(self, n: State[int]):
        super().__init__(n)
        self._num: State[int] = n

    def view(self):
        return Column(
             Button(“Add”).fixed_height(40).on_click(lambda _: self.num.set(self._num() + 1)),
             *(Text(i + 1).fixed_height(40) for i in range(self._num())),
             scrollable=True,
        )

App(Frame("NumList"), NumList(State(1))).run()
```

<div class="demo">
    <iframe width="100%" height="100%" src="../examples/num_list.html"></iframe>
</div>

This component adds a new text with number when the Add button is clicked.
It has an underscore num instance variable as state. It must also be passed to the constructor of the state component class.
In this way, the view of the entire NumList is updated when the value of `_num` instance variable is updated. In other words, it’s like that the entire view method is reexecuted on updating the state of component.
