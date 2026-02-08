"""Example usage of ConfigKit for application configuration."""

from configkit import ConfigKit


class AppConfiguration(ConfigKit):
    """Application configuration with database settings."""

    def additional_checks(self) -> None:
        """Validate database section exists."""
        if "database" not in self.data:
            raise ValueError("'database' section is required")

    def get_db_host(self) -> str:
        """Return database host."""
        return self.get("database.host")

    def get_db_port(self) -> int:
        """Return database port with default fallback."""
        return self.get("database.port", default=5432)


class YamlConfiguration(ConfigKit):
    """Same configuration loaded from a YAML file."""

    def additional_checks(self) -> None:
        """Validate database section exists."""
        if "database" not in self.data:
            raise ValueError("'database' section is required")


def main() -> None:
    """Demonstrate ConfigKit usage with JSON and YAML configs."""
    # JSON configuration
    AppConfiguration(
        config_file="./example/config.json",
        schema_file="./example/schema.json",
    )
    config = AppConfiguration()
    print("=== JSON Config ===")
    print(f"Database host: {config.get_db_host()}")
    print(f"Database port: {config.get_db_port()}")

    # YAML configuration (separate subclass = separate singleton instance)
    YamlConfiguration(
        config_file="./example/config.yaml",
        schema_file="./example/schema.json",
    )
    yaml_config = YamlConfiguration()
    print("\n=== YAML Config ===")
    print(f"Database host: {yaml_config.get('database.host')}")
    print(f"Database port: {yaml_config.get('database.port')}")


if __name__ == "__main__":
    main()
