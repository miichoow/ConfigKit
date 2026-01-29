# ConfigKit

Thread-safe singleton JSON configuration loader with JSON Schema validation for Python applications.

## Features

- **Thread-safe singleton** - One instance per configuration class
- **JSON Schema validation** - Draft 2020-12 support via `jsonschema`
- **Dot-notation access** - `config.get("database.host")`
- **Runtime reload** - Update configuration without restart
- **Type-safe** - Full type hints with `py.typed` marker
- **Extensible** - Custom validation via `additional_checks()`

## Installation

### From PyPI

```bash
pip install pyConfigKit
```

### From Git repository

```bash
pip install git+https://github.com/miichoow/ConfigKit.git
```

### Development mode

```bash
git clone https://github.com/miichoow/ConfigKit.git
cd ConfigKit
pip install -e ".[dev]"
```

## Quick Start

### 1. Create your configuration class

```python
from configkit import ConfigKit


class AppConfig(ConfigKit):
    def additional_checks(self) -> None:
        # Custom validation logic
        if self.data.get("debug") and self.data.get("env") == "production":
            raise ValueError("Debug mode not allowed in production")

    def get_database_url(self) -> str:
        host = self.get("database.host")
        port = self.get("database.port", default=5432)
        name = self.get("database.name")
        return f"postgresql://{host}:{port}/{name}"
```

### 2. Create configuration files

**config.json**
```json
{
  "env": "development",
  "debug": true,
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "myapp"
  }
}
```

**schema.json**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["env", "database"],
  "properties": {
    "env": {
      "type": "string",
      "enum": ["development", "staging", "production"]
    },
    "debug": {
      "type": "boolean"
    },
    "database": {
      "type": "object",
      "required": ["host", "name"],
      "properties": {
        "host": { "type": "string" },
        "port": { "type": "integer", "minimum": 1, "maximum": 65535 },
        "name": { "type": "string" }
      }
    }
  }
}
```

### 3. Use in your application

```python
# Initialize once at startup
config = AppConfig(json_file="config.json", schema_file="schema.json")

# Access anywhere - returns the same instance
config = AppConfig()
print(config.get_database_url())
```

## API Reference

### ConfigKit

Base class for configuration. Subclass and implement `additional_checks()`.

#### Constructor

```python
ConfigKit(*, json_file: str | Path, schema_file: str | Path)
```

- `json_file` - Path to JSON configuration file
- `schema_file` - Path to JSON Schema file

#### Properties

| Property | Type             | Description                     |
|----------|------------------|---------------------------------|
| `data`   | `dict[str, Any]` | Loaded configuration dictionary |
| `schema` | `dict[str, Any]` | Loaded JSON Schema dictionary   |

#### Methods

| Method                       | Description                      |
|------------------------------|----------------------------------|
| `get(path, *, default=None)` | Get value by dot-notation path   |
| `reload()`                   | Reload and re-validate from disk |
| `additional_checks()`        | Override for custom validation   |

### ConfigKitMeta

Metaclass providing singleton behavior.

| Method    | Description                                 |
|-----------|---------------------------------------------|
| `reset()` | Clear all singleton instances (for testing) |

## Design Principles

- **Fail fast** - Invalid configuration raises exceptions immediately
- **Single source of truth** - One instance per configuration class
- **Explicit contracts** - Required files on first instantiation
- **No magic** - Clear, predictable behavior

## Publishing

```bash
pip install -e ".[dev]"
python -m build
twine upload dist/*
```

## License

MIT License - see [LICENSE](./LICENSE) for details.
