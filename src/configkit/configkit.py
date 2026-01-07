from __future__ import annotations

from jsonschema import Draft202012Validator, ValidationError
from typing import Any, Dict, Optional

import json
import os
import threading


class ConfigKitMeta(type):
    """
    Thread-safe singleton metaclass enforcing:
    - single instance per concrete class
    - mandatory configuration files on first instantiation
    """

    _instances: Dict[type, "ConfigKit"] = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
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
    def _reset(cls) -> None:
        """Internal helper for tests or controlled resets."""
        cls._instances.clear()


class ConfigKit(metaclass=ConfigKitMeta):
    """
    Base class for JSON configuration loading and validation.

    Subclasses must implement `additional_checks`.
    """

    def __init__(self, *, json_file: Optional[str] = None, schema_file: Optional[str] = None) -> None:
        if not json_file or not schema_file:
            raise ValueError("First instantiation requires 'json_file' and 'schema_file'")
        self._json_file = json_file
        self._schema_file = schema_file

        self._check_files()
        self._load_files()
        self._validate_schema()
        self.additional_checks()

    # =============================
    # File handling
    # =============================
    def _check_files(self) -> None:
        for path in (self._json_file, self._schema_file):
            if not os.path.isfile(path):
                raise FileNotFoundError(f"File does not exist: {path}")
            if not os.access(path, os.R_OK):
                raise PermissionError(f"File is not readable: {path}")

    def _load_files(self) -> None:
        self.data = self._load_json(self._json_file)
        self.schema = self._load_json(self._schema_file)

    @staticmethod
    def _load_json(path: str) -> Dict[str, Any]:
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in '{path}': {exc}") from exc

    # =============================
    # Validation
    # =============================
    def _validate_schema(self) -> None:
        try:
            Draft202012Validator(self.schema).validate(self.data)
        except ValidationError as exc:
            raise ValueError(
                f"Configuration does not match schema: {exc.message}"
            ) from exc

    # =============================
    # Public API
    # =============================
    def get(self, path: str, *, default: Any = None) -> Any:
        """
        Retrieve a value using dot-notation.

        Example:
            config.get("database.host")
        """
        current: Any = self.data
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                if default is not None:
                    return default
                raise KeyError(f"Missing configuration key: '{path}'")
            current = current[key]
        return current

    def reload(self) -> None:
        """
        Reload configuration from disk and re-validate.
        """
        self._check_files()
        self._load_files()
        self._validate_schema()
        self.additional_checks()

    # =============================
    # Extension point
    # =============================
    def additional_checks(self) -> None:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement additional_checks()"
        )
