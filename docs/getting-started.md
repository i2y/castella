## Prerequisite
Castella requires the version of Python >= `3.11`.

## For Desktop
Castella for Desktop depends on either GLFW or SDL2, so the installation method of Castella differs slightly depending on which one is used. I recommend using GLFW since Castella with GLFW currently performs better.

In any case, Castella installation is usually completed with a single `pip install`.

### In case of using Castella with GLFW

You can install Castella from PyPI with the following command.
```
$ pip install castella[glfw]
```

Instead using PyPI, to install the latest Castella source code from GitHub, you can execute the following command.
```
$ pip install "git+https://github.com/i2y/castella.git"[glfw]
```

If you run the above command in PowerShell on Windows it may fail. In that case, please clone the git repository as follows and then do `pip install .[glfw]`.
```
$ git clone git+https://github.com/i2y/castella.git
$ cd castella
$ pip install .[glfw]
```

#### If you want to install another GLFW shared library
GLFW shared library itself would be installed with the above command, but if you'd like to install another GFLW shared library, you can do it as well.
Also, the only `pip install castella[glfw]` may cause glfw-related errors. In that case, please try additionally this installation procedure.

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


### In case of using Castella with SDL2
You can install Castella from PyPI with the following command.
```
$ pip install castella[sdl]
```

Instead using PyPI, to install the latest Castella source code from GitHub, you can execute the following command.
```
$ pip install "git+https://github.com/i2y/castella.git"[sdl]
```

If you run the above command in PowerShell on Windows it may fail. In that case, please clone the git repository as follows and then do `pip install .[sdl]`.
```
$ git clone git+https://github.com/i2y/castella.git
$ cd castella
$ pip install .[sdl]
```

#### If you want to install another SDL2 shared library
SDL2 shared library itself would be installed with the above command, but if you'd like to install another SDL2 shared library, you can do it as well.

You can download and use precompiled version from [this page](https://www.libsdl.org/download-2.0.php).

After downloading and storing it, please set the installed folder path to the environment variable `PYSDL2_DLL_PATH`.
(For more information on how PySDL2 finds SDL2 DLL, see [this page](https://pysdl2.readthedocs.io/en/rel_0_9_7/integration.html).)

### Confirmation of successful installation
If the installation was successful, then [hello_world.py](https://github.com/i2y/castella/blob/main/examples/hello_world.py), [calc.py](https://github.com/i2y/castella/blob/main/examples/calc.py), etc. under [the examples folder](https://github.com/i2y/castella/tree/main/examples) will work.


## For Web Browsers
Here, we are going to explain how to use Castella in your PyScript app.

For more information on how to write a PyScript app, please refer to [the official documentation](https://pyscript.net/).

For now, to use Castella on an html page, you need to do something as the following.

- Load the pyscript JS file and the canvaskit JS file and initialize it properly in your html
- Specify all Castella modules to be used in the html page in pyscript config file (`pyscript.toml`)
- Serve the html page and modules with any web server.

A tiny example of the above procedure is shown below.

##### 1. Create your app folder

```sh
$ mkdir counter
```

##### 2. Clone Castella repository

```sh
$ cd counter
$ git clone git@github.com:i2y/castella.git
```

##### 3. Implement your app
You need to create `counter.html` file with the following content in your app folder.
```html
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <title>Misc</title>
    <link rel="stylesheet" href="https://pyscript.net/releases/2024.4.1/core.css">
    <script type="module" src="https://pyscript.net/releases/2024.4.1/core.js"></script>
    <script type="text/javascript" src="https://unpkg.com/canvaskit-wasm@0.33.0/bin/canvaskit.js"></script>
</head>
<body>
<script type="py" src="counter.py" config="pyscript.toml"></script>
</body>
</html>
```

Then, you need to write `pyscript.toml` file with the following content in your app folder.
```toml
packages = [ "./castella-0.1.13-py3-none-any.whl" ]
```

Next, off course, you need to create `counter.py` file with the following content in your app folder.
```python
from castella import App, Button, Column, Component, Row, State, Text
from castella.frame import Frame


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


if __name__ == "__main__":
    App(Frame("Counter", 800, 600), Counter()).run()
```


##### 4. Serve your app
Finally, could please serve your app using http server.
```sh
$ python -m http.server 3000
```
Now, you can see the UI of counter app at [http://127.0.0.1:3000/counter.html](http://127.0.0.1:3000/counter.html) using any web browser.
That will be shown as the following.

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

The above counter app is emmbeded in an iframe.
