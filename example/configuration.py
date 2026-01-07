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
