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


def main() -> None:
    """Demonstrate ConfigKit usage."""
    AppConfiguration(
        json_file="./example/config.json",
        schema_file="./example/schema.json",
    )

    config = AppConfiguration()
    print(f"Database host: {config.get_db_host()}")
    print(f"Database port: {config.get_db_port()}")


if __name__ == "__main__":
    main()
