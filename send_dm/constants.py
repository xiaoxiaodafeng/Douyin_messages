from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent

DEFAULT_SEC_UID = "MS4wLjABAAAA6nwCMmI1iiLvBJmFrspie33H3k_w-N_O4vexWNLFw1g"
DEFAULT_PROFILE = PROJECT_DIR.parent / ".pw-douyin-profile"

DEFAULT_ENV_CANDIDATES = [
    PROJECT_DIR / ".env",
    PROJECT_DIR.parent / "Douyin_Spider" / ".env",
]
