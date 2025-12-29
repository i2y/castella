# Hot Reloading

!!! note "Experimental Feature"
    Hot reloading is an experimental feature with limited support. For reliable development workflows, use [Hot Restarting](hot-restarting.md) instead.

## Overview

Hot reloading updates running code without restarting the application, preserving application state. This provides faster iteration than hot restarting since only changed modules are reloaded.

## Current Status

Hot reloading in Castella is currently limited due to the complexity of:

- Preserving widget tree state across reloads
- Updating event handlers that reference old class instances
- Managing component lifecycle during reload

For most development workflows, [Hot Restarting](hot-restarting.md) is recommended.

## Web Development

For web applications using PyScript/Pyodide, you can use your browser's built-in development tools:

1. Use your development server's live reload feature
2. The browser will refresh when files change
3. This is effectively hot restarting at the browser level

## Alternatives

### Hot Restarting (Recommended)

Use the hot restarter for reliable code updates:

```bash
uv run python tools/hot_restarter.py your_app.py
```

See [Hot Restarting](hot-restarting.md) for details.

### Manual Reload

For quick experiments, you can manually restart your application after making changes.

## Future Plans

Full hot reloading support for Component classes is planned for future releases. This would allow:

- Updating `view()` methods without restart
- Preserving `State` values across reloads
- Live style and layout adjustments

## Technical Challenges

Implementing hot reloading in a GUI framework requires solving:

1. **Class identity**: When a module is reloaded, classes are recreated with new identities. Existing instances still reference old classes.

2. **Event handlers**: Lambda functions and method references capture the original class/instance.

3. **State preservation**: Transferring state from old instances to new instances requires careful introspection.

4. **Widget tree**: The component hierarchy must be updated while maintaining parent-child relationships.

These challenges make hot restarting the more practical choice for most development scenarios.
