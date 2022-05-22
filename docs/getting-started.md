## For Desktop
Cattt for Desktop depends on either GLFW or SDL2, so the installation method of Cattt differs slightly depending on which one is used. I recommend using GLFW since Cattt with GLFW currently performs better.


### In case of using Cattt with GLFW

You can install Cattt with the following command.
```
$ pip install cattt[glfw]
```

If GLFW is not already installed in your environment, please install it as well.

For Windows/Mac/Linux, you can download and use precompiled version from [this page](https://www.glfw.org/download.html). Please follow its instructions to install.

For Mac and Linux, you can also install using a package manager.

Mac

```
$ brew install glfw3
```

Linux

```
$ sudo apt-get install -y libglfw3-dev
```
or
```
$ sudo yum install -y libglfw3-dev
```


### In case of using Cattt with SDL2
You can install Cattt with the following command.
```
$ pip install cattt[sdl]
```

If SDL2 is not already installed in your environment, please install it as well.
You can download and use precompiled version from [this page](https://www.libsdl.org/download-2.0.php).

After downloading and storing it, please set the installed folder path to the environment variable `PYSDL2_DLL_PATH`.
(For more information on how PySDL2 finds SDL2 DLL, see [this page](https://pysdl2.readthedocs.io/en/rel_0_9_7/integration.html).)


## For Web Browsers
Sorry, we have not yet established a clean and easy way to do this.
Here, for now, we will explain how to use Cattt in your PyScript app.

For more information on how to write a PyScript app, please refer to [the official documentation](https://pyscript.net/).

For now, to use Cattt on an html page, you need to do something as the following.

- Load the pyscript JS file canvaskit JS file and initialize it properly in your html
- Specify all Cattt modules to be used in the html page with py-env tag.
- Serve the html page and modules with any web server.

A tiny example of the above procedure is shown below.

##### 1. Create your app folder

```sh
$ mkdir counter
```

##### 2. Clone Cattt repository

```sh
$ cd counter
$ git clone git@github.com:i2y/cattt.git
```

##### 3. Implement your app
Please create `counter.html` file with the following content in your app folder.
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />

    <title>Counter</title>
    <link rel="stylesheet" href="https://pyscript.net/alpha/pyscript.css" />
    <script type="text/javascript" src="https://unpkg.com/canvaskit-wasm@0.33.0/bin/canvaskit.js"></script>
    <script defer src="https://pyscript.net/alpha/pyscript.js"></script>
</head>
<py-env>
    - numpy
    - paths:
        - cattt/cattt/color.py
        - cattt/cattt/core.py
        - cattt/cattt/web_frame.py
        - cattt/cattt/frame.py
        - cattt/cattt/canvaskit_painter.py
</py-env>
<py-script>
from core import App, Column, Row, Button, Text, State, Component, SizePolicy
from frame import Frame


class Counter(Component):
    def __init__(self):
        super().__init__()
        self._count = State(0)

    def view(self):
        return Column(
            Text(self._count),
            Row(Button("Up").on_click(self.up), Button("Down").on_click(self.down)),
        )

    def up(self, _):
        self._count += 1

    def down(self, _):
        self._count -= 1

App(Frame("Counter"), Counter()).run()
</py-script>
</html>
```

##### 4. Serve your app
Finally, please serve your app using http server.
```sh
$ python -m http.server 3000
```
Please open [http://127.0.0.1:3000/counter.html](http://127.0.0.1:3000/counter.html) with any browser.

Or, you can use live preview your app with Visual Studio Code or something like that.

<video width="800" height="600" controls>
    <source src="/counter.mp4" type="video/mp4">
</video>
