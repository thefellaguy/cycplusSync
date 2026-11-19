from __future__ import annotations

from pathlib import Path
from typing import Tuple, Type

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


_CONFIG_FILE = Path.home() / ".cycplusSync" / "config.toml"


class Settings(BaseSettings):
    target_name: str = Field(default="M1_B0ED", description="BLE device name to scan for")
    target_mac_address: str = Field(default="", description="Optional MAC address; skips scan if set")
    profile: str = Field(default="Default", description="Profile name; rides stored under ~/.cycplusSync/profiles/<profile>/rides")

    model_config = SettingsConfigDict(
        env_prefix="CYCPLUSSYNC_",
        toml_file=str(_CONFIG_FILE),
        cli_parse_args=True,
        cli_prog_name="cycplusSync",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # Priority: CLI > env > toml > defaults
        from pydantic_settings import CliSettingsSource
        return (
            CliSettingsSource(settings_cls, cli_parse_args=True),
            env_settings,
            TomlConfigSettingsSource(settings_cls),
        )
