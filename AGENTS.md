# Repository Instructions

## Model Boundaries

- Use Pydantic only for deserializing and validating JSON payloads returned by the
  Sonance device HTTP API.
- Keep Pydantic models private to the library implementation. Wire-format models
  belong in `src/sonance_py/_wire_models.py`.
- Public library APIs must return simple stdlib dataclasses from
  `src/sonance_py/models.py`.
- Do not expose Pydantic `BaseModel` subclasses from `sonance_py.__init__`,
  client methods, or other public APIs.
- If a new device endpoint is added, model the raw JSON shape in `_wire_models.py`
  first, then convert it to a public dataclass before returning it to callers.
