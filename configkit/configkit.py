"""Core module for ConfigKit configuration management."""

from __future__ import annotations

import json
import threading
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from jsonschema import Draft202012Validator, ValidationError

if TYPE_CHECKING:
    from collections.abc import Iterator


class ConfigKitMeta(type):
    """Thread-safe singleton metaclass for configuration classes.

    Ensures one instance per concrete subclass using double-checked locking.
    First instantiation requires `json_file` and `schema_file` parameters.
    """

    _instances: ClassVar[dict[type, ConfigKit]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> ConfigKit:
        """Return existing instance or create new one with validation."""
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    if not kwargs.get("json_file") or not kwargs.get("schema_file"):
                        raise ValueError(
                            "First instantiation requires 'json_file' and 'schema_file'"
                        )
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def reset(mcs) -> None:
        """Clear all singleton instances. Use for testing or controlled resets."""
        with mcs._lock:
            mcs._instances.clear()


class ConfigKit(metaclass=ConfigKitMeta):
    """Base class for JSON configuration with schema validation.

    Subclasses must implement the `additional_checks` method for custom validation.

    Example:
        >>> class AppConfig(ConfigKit):
        ...     def additional_checks(self) -> None:
        ...         if self.data.get("debug") and self.data.get("production"):
        ...             raise ValueError("Cannot enable debug in production")
        ...
        >>> config = AppConfig(json_file="config.json", schema_file="schema.json")
        >>> config.get("database.host")
        'localhost'
    """

    __slots__ = ("_json_path", "_schema_path", "_data", "_schema")

    def __init__(
        self,
        *,
        json_file: str | Path | None = None,
        schema_file: str | Path | None = None,
    ) -> None:
        """Initialize configuration from JSON file with schema validation.

        Args:
            json_file: Path to the JSON configuration file.
            schema_file: Path to the JSON Schema file.

        Raises:
            ValueError: If files are not provided on first instantiation.
            FileNotFoundError: If files do not exist.
            PermissionError: If files are not readable.
        """
        if not json_file or not schema_file:
            raise ValueError("First instantiation requires 'json_file' and 'schema_file'")

        self._json_path = Path(json_file)
        self._schema_path = Path(schema_file)
        self._data: dict[str, Any] = {}
        self._schema: dict[str, Any] = {}

        self._validate_paths()
        self._load()
        self._validate_against_schema()
        self.additional_checks()

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"{self.__class__.__name__}(json_file={self._json_path!r})"

    @property
    def data(self) -> dict[str, Any]:
        """Return the loaded configuration data."""
        return self._data

    @property
    def schema(self) -> dict[str, Any]:
        """Return the loaded JSON schema."""
        return self._schema

    def _validate_paths(self) -> None:
        """Verify configuration files exist and are readable."""
        for path in (self._json_path, self._schema_path):
            if not path.is_file():
                raise FileNotFoundError(f"File not found: {path}")
            try:
                with path.open():
                    pass
            except PermissionError:
                raise PermissionError(f"File not readable: {path}") from None

    def _load(self) -> None:
        """Load JSON configuration and schema files."""
        self._data = self._parse_json(self._json_path)
        self._schema = self._parse_json(self._schema_path)

    @staticmethod
    def _parse_json(path: Path) -> dict[str, Any]:
        """Parse JSON file and return contents.

        Args:
            path: Path to JSON file.

        Returns:
            Parsed JSON as dictionary.

        Raises:
            ValueError: If JSON is malformed.
        """
        try:
            with path.open(encoding="utf-8") as file:
                content: dict[str, Any] = json.load(file)
                return content
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in '{path}': {exc}") from exc

    def _validate_against_schema(self) -> None:
        """Validate configuration data against JSON schema."""
        try:
            Draft202012Validator(self._schema).validate(self._data)
        except ValidationError as exc:
            raise ValueError(f"Schema validation failed: {exc.message}") from exc

    def get(self, path: str, *, default: Any = None) -> Any:
        """Retrieve value using dot-notation path.

        Args:
            path: Dot-separated key path (e.g., "database.host").
            default: Value to return if path not found.

        Returns:
            Configuration value or default.

        Raises:
            KeyError: If path not found and no default provided.

        Example:
            >>> config.get("database.port", default=5432)
            5432
        """
        current: Any = self._data
        for key in self._iter_path(path):
            if not isinstance(current, dict) or key not in current:
                if default is not None:
                    return default
                raise KeyError(f"Configuration key not found: '{path}'")
            current = current[key]
        return current

    @staticmethod
    def _iter_path(path: str) -> Iterator[str]:
        """Iterate over dot-separated path segments."""
        return iter(path.split("."))

    def reload(self) -> None:
        """Reload configuration from disk and re-validate.

        Useful for runtime configuration updates without restart.
        """
        self._validate_paths()
        self._load()
        self._validate_against_schema()
        self.additional_checks()

    @abstractmethod
    def additional_checks(self) -> None:
        """Perform custom validation logic.

        Override this method to implement domain-specific validation
        that cannot be expressed in JSON Schema.

        Raises:
            ValueError: If custom validation fails.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement additional_checks()"
        )
