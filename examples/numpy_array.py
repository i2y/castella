import matplotlib.pyplot as plt
import numpy as np
from castella import App, Button, Column, NumpyImage, Row
from castella.frame import Frame
from matplotlib import cm
from matplotlib.ticker import LinearLocator

# I copied and pasted matplotlib part from https://note.com/tukkidney/n/nf6f8af2ec281
array = np.zeros((640, 640, 4), dtype=np.uint8)
array[:, :, 3] = 255

fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

X = np.arange(-5, 5, 0.25)
Y = np.arange(-5, 5, 0.25)
X, Y = np.meshgrid(X, Y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm, linewidth=0, antialiased=False)

ax.set_zlim(-1.01, 1.01)
ax.zaxis.set_major_locator(LinearLocator(10))
ax.zaxis.set_major_formatter("{x:.02f}")
ax.patch.set_alpha(0)

fig.patch.set_alpha(0.1)

fig.canvas.draw()
array = np.array(fig.canvas.renderer.buffer_rgba())

App(
    Frame(title="NumPy Images", width=800, height=600),
    Column(
        Row(NumpyImage(array), NumpyImage(array), scrollable=True)
        .fixed_height(500)
        .spacing(20),
        Row(
            NumpyImage(array),
            Button("button").fixed_width(200),
            NumpyImage(array),
            scrollable=True,
        )
        .fixed_height(500)
        .spacing(20),
        scrollable=True,
    ).spacing(20),
).run()
