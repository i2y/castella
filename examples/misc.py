from cattt.core import (App, Box, Button, Column, Component, Image, Input, Kind,
                       NetImage, Row, SizePolicy, Spacer, State,
                       StatefulComponent, Text)
from cattt.frame import Frame


class Counter(Component):
    def __init__(self, count: State[int]):
        super().__init__()
        self.count = count

    def view(self):
        c = self.count
        return Row(Button("Up").on_click(lambda _: c.set(c() + 1)),
                   Text(self.count),
                   Button("Down").on_click(lambda _: c.set(c() - 1)))


class NumList(StatefulComponent):
    def __init__(self, n: State[int]):
        super().__init__(n)
        self.num: State[int] = n

    def view(self):
        return Column(*(Text(i+1).fixed_height(30) for i in range(self.num())), scrollable=True)


DOME_TENT_IMG = "https://3.bp.blogspot.com/-NZBf8tr3fcM/WZP3V2hKZBI/AAAAAAABF9g/Yyr1CVNNnCE9HhL10-hYfMSHUF7c9VbsQCLcBGAs/s800/camp_tent_maru.png"

c: State[int] = State(0)

App(Frame(title="Counter", width=800, height=600),
    Column(Counter(c),
           Spacer().fixed_height(20),
           Box(Row(Image(file_path="camp_tent_sankaku.png"), NetImage(url=DOME_TENT_IMG))
               .size_policy(SizePolicy.CONTENT)),
           NumList(c),
           Input("fafa"))).run()
