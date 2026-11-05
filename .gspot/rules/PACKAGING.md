# Python packaging

Read this rule when you change Python dependencies, lockfiles, or package layout.

## Lockfiles

Update lockfiles only when the task includes dependency maintenance.

## Scripts

A standalone script has a shebang and the executable bit.

## Packages and architecture

- Keep packages shallow and purposeful.
- Flatten packages that contain only `__init__.py` and one other module.
- Do not use package `__init__.py` files to hide expensive imports.
- Keep `__init__.py` files small and import-stable.
- A package `__init__.py` holds no re-exports. A library that publishes its API through `__init__.py` asks the user to
  set `structure.reexports` to `index-only`.
- Keep lower-level packages independent of higher-level workflows.

## Source layout

Keep the layout the project has. A new package puts its code under `src/`:

```text
pyproject.toml
src/
  order_service/
    __init__.py
    orders.py
    accounts.py
```

Keep unimported helper scripts outside the package import path.
