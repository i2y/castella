# Hot Restarting

Hot restarting automatically restarts your Castella application whenever source files change, enabling rapid development iteration.

## Usage

Use the `hot_restarter.py` tool from the `tools/` directory:

```bash
# With uv (recommended)
uv run python tools/hot_restarter.py your_app.py

# With regular Python
python tools/hot_restarter.py examples/counter.py
```

## How It Works

1. The tool starts your application as a subprocess
2. It watches all `.py` files in the current directory (recursively)
3. When any `.py` file is modified:
   - The current application process is killed
   - A new instance is started immediately
4. If the application crashes, it automatically restarts

## Requirements

The hot restarter requires the `watchdog` library:

```bash
# With uv (recommended)
uv add watchdog

# With pip
pip install watchdog
```

This is included in the development dependencies:

```bash
# With uv
uv sync --extra dev

# With pip
pip install -e ".[dev]"
```

## Example Workflow

1. Start your app with hot restarting:
   ```bash
   uv run python tools/hot_restarter.py examples/counter.py
   ```

2. Edit your code in your editor

3. Save the file - the app automatically restarts with your changes

4. Press `Ctrl+C` to stop the watcher and application

## Behavior Details

### Watched Files

- All `.py` files in the current directory and subdirectories
- Changes to any Python file trigger a restart

### Restart Triggers

- File modifications (saving a file)
- The previous process crashing or exiting

### Process Management

- Only one instance runs at a time
- The previous instance is killed before starting a new one
- Clean shutdown on `Ctrl+C`

## Limitations

- **Full restart**: The entire application restarts, not just the modified module
- **State loss**: All application state is lost on restart
- **Window position**: Window position may reset on restart
- **Startup time**: Each restart incurs full application startup time

## Tips

1. **Keep initialization fast**: Since the app restarts completely, fast startup improves your iteration speed

2. **Use for UI development**: Hot restarting is ideal for tweaking layouts, styles, and widget properties

3. **Combine with logging**: Add print statements or logging to debug issues between restarts

## Comparison with Hot Reloading

| Feature | Hot Restarting | Hot Reloading |
|---------|---------------|---------------|
| State preserved | No | Yes |
| Startup time | Full restart | Incremental |
| Reliability | High | Experimental |
| Implementation | Simple subprocess | Complex module reload |

For most development workflows, hot restarting provides a reliable and predictable experience.
