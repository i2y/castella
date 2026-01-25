from castella import App, Button, Column, Component, Row, State, Text, TextAlign, Widget
from castella.frame import Frame


class Calc(Component):
    def __init__(self):
        super().__init__()
        self.result = State("0")
        self._all_clear()

    def press_number(self, ev):
        if self.result.value() == "0" or self.is_refresh:
            self.prev_result = self.result.value()
            self.result.set(ev.target.get_label())
        else:
            self.result += ev.target.get_label()
        self.is_refresh = False

    def press_dot(self, ev):
        if "." in self.result.value():
            return

        if self.is_refresh:
            self.prev_result = self.result.value()
            self.result.set(ev.target.get_label())
        else:
            self.result.set(self.result.value() + ev.target.get_label())
        self.is_refresh = False

    def all_clear(self, _):
        self._all_clear()

    def _all_clear(self):
        self.result.set("0")
        self.prev_result = None
        self.operator = ""
        self.is_refresh = False

    def press_operator(self, ev):
        op = self.operator
        new_op = ev.target.get_label()

        if op == "":
            if new_op == "=":
                self.all_clear(ev)
            self.is_refresh = True
            self.operator = new_op
            return

        if self.prev_result is None or self.result.value() is None:
            return
        lhs = str(self.prev_result)
        rhs = self.result.value()
        result = Calc.calc(lhs, op, rhs)
        result_str = str(result)
        if result_str[-2:] == ".0":
            result_str = result_str[0:-2]
        self.result.set(result_str)

        if new_op == "=":
            self.is_refresh = True
            self.operator = ""
        else:
            self.operator = new_op
            self.is_refresh = True

    def view(self) -> Widget:
        return Column(
            Text(self.result, align=TextAlign.RIGHT),
            Row(self.ac().flex(3), self.op("÷")),
            Row(self.number(7), self.number(8), self.number(9), self.op("×")),
            Row(self.number(4), self.number(5), self.number(6), self.op("-")),
            Row(self.number(1), self.number(2), self.number(3), self.op("+")),
            Row(self.number(0).flex(2), self.dot(), self.op("=")),
        )

    def number(self, num: int) -> Button:
        return Button(str(num), font_size=50).on_click(self.press_number)

    def dot(self) -> Button:
        return Button(".", font_size=50).on_click(self.press_dot)

    def ac(self) -> Button:
        return Button("AC", font_size=50).on_click(self.all_clear)

    def op(self, label: str) -> Button:
        return Button(label, font_size=50).on_click(self.press_operator)

    @staticmethod
    def calc(lhs: str, op: str, rhs: str):
        if op == "+":
            return float(lhs) + float(rhs)
        elif op == "-":
            return float(lhs) - float(rhs)
        elif op == "×":
            return float(lhs) * float(rhs)
        elif op == "÷":
            return float(lhs) / float(rhs)


if __name__ == "__main__":
    App(
        Frame("Calc", width=400, height=600),
        Calc(),
    ).run()
