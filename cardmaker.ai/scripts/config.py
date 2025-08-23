import os


def get_env(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value


class Settings:
    def __init__(self) -> None:
        # ComfyUI
        self.COMFY_HOST: str = get_env("COMFY_HOST", "http://localhost:8188")
        self.COMFY_TIMEOUT_S: int = int(get_env("COMFY_TIMEOUT_S", "120"))
        # Optional workflow inputs depending on your setup
        self.COMFY_WORKFLOW_ID: str = get_env("COMFY_WORKFLOW_ID", "")
        self.COMFY_PROMPT_INPUT_KEY: str = get_env("COMFY_PROMPT_INPUT_KEY", "prompt")
        self.COMFY_WORKFLOW_PATH: str = get_env(
            "COMFY_WORKFLOW_PATH",
            os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                "art-generation.json",
            ),
        )
        self.COMFY_CLIENT_ID: str = get_env("COMFY_CLIENT_ID", "deckport-ai")

        # Files and paths
        self.PROJECT_ROOT: str = get_env(
            "PROJECT_ROOT",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        )
        self.ASSET_ROOT: str = get_env("ASSET_ROOT", os.path.join(self.PROJECT_ROOT, ""))
        self.OUTPUT_DIR: str = get_env("OUTPUT_DIR", os.path.join(self.PROJECT_ROOT, "cards_output"))
        # Prefer Chakra Petch if present, else fallback to system default
        default_font = os.path.join(self.PROJECT_ROOT, "Chakra_Petch", "ChakraPetch-SemiBold.ttf")
        if not os.path.exists(default_font):
            default_font = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        self.FONT_PATH: str = get_env("FONT_PATH", default_font)
        self.CARD_ELEMENTS_DIR: str = get_env(
            "CARD_ELEMENTS_DIR",
            os.path.join(self.PROJECT_ROOT, "card_elements"),
        )

        # Database
        self.DATABASE_URL: str = get_env(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/deckport"
        )
        self.SQLITE_DB_PATH: str = get_env("SQLITE_DB_PATH", "")
        self.SQLITE_SCHEMA_PATH: str = get_env("SQLITE_SCHEMA_PATH", "")

        # Defaults for SQLite if not provided
        if not self.SQLITE_DB_PATH:
            self.SQLITE_DB_PATH = os.path.join(self.PROJECT_ROOT, "deckport.sqlite3")
        if not self.SQLITE_SCHEMA_PATH:
            self.SQLITE_SCHEMA_PATH = os.path.join(self.PROJECT_ROOT, "db", "schema.sqlite.sql")

        # Render
        self.CANVAS_W: int = int(get_env("CANVAS_W", "1500"))
        self.CANVAS_H: int = int(get_env("CANVAS_H", "2100"))


settings = Settings()

