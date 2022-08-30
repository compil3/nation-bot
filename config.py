#Config validator.
from dynaconf import Dynaconf, Validator


class ConfigLoader:
    def __init__(self):
        self.settings = self.load_settings()

    def get_settings(self):
        return self.settings

    def load_settings():
        settings = Dynaconf(
            settings_files=["configs/settings.json", "configs/.secrets.json"],
            environments=True,
            load_dotenv=True,
            env_switcher="ENV_FOR_DYNACONF",
            dotenv_path="configs/.dynaenv",
        )

        settings.validators.register(Validator("DISCORD_TOKEN", "_DEV_TOKEN", "DATABASE_ADDRESS", "SPARKEDHOST", must_exist=True))
        settings.validators.validate()

        return settings
    