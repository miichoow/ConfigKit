# ConfigKit

ConfigKit is a Python library for loading, validating and accessing JSON configuration files in a safe and structured way.

It enforces:
- Singleton configuration loading
- JSON Schema validation
- Thread safety
- Clean extension points
- Early failure on misconfiguration

## Features

* Thread-safe singleton 
* JSON Schema validation (Draft 2020-12)
* Dot-notation access (config.get("a.b.c"))
* Reload support 
* Clean subclass contract 
* Pip-installable without PyPI

## Design Principles

* Configuration is loaded once and reused
* Validation fails fast
* No global variables
* Explicit extension points
* Minimal magic

## Installation

### From local directory

```bash
pip install .
```

### From Git repository

```bash
pip install https://github.com/miichoow/ConfigKit.git
```

## Basic Usage

```python
from configkit.configkit import ConfigKit


class Configuration(ConfigKit):
    def additional_checks(self) -> None:
        if "database" not in self.data:
            raise ValueError("'database' section is required")

    def get_db_host(self) -> str:
        return self.get("database.host")

    def get_db_port(self) -> int:
        return self.get("database.port", default=5432)


if __name__ == "__main__":
    try:
        Configuration(json_file="./example/config.json", schema_file="./example/schema.json")
        configuration = Configuration()
        print(configuration.get_db_host())
        print(configuration.get_db_port())
    except Exception as e:
        print(e)
```

## License

See [LICENSE](./LICENSE) file.
