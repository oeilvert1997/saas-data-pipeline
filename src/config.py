import secrets
from pathlib import Path
from urllib.parse import urlencode

import yaml


class CompanyConfig:
    """
    comment
    """

    def __init__(self, name: str, data: dict, shared: dict):
        self.name = name
        self.client_id: str = shared["client_id"]
        self.client_secret: str = shared["client_secret"]
        self.redirect_uri: str = shared.get(
            "redirect_uri", "http://localhost:8000/callback"
        )
        self.company_id: int = int(data.get("company_id", 0))
        self.token_file: Path = Path(data.get("token_file", f"tokens/{name}.json"))
        self.data_dir: Path = Path(data.get("data_dir", f"data/{name}"))

        # comment
        self.authorize_url: str = (
            "https://accounts.secure.freee.co.jp/public_api/authorize"
        )
        self.token_url: str = "https://accounts.secure.freee.co.jp/public_api/token"
        self.account_api_url: str = "https://api.freee.co.jp/api/1/"
        self.hr_api_url: str = "https://api.freee.co.jp/hr/api/v1/"

        # comment
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def generate_auth_url(self) -> tuple[str, str]:
        """
        comment
        """
        state = secrets.token_urlsafe(32)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "prompt": "select_company",
        }

        query = urlencode(params)
        return f"{self.authorize_url}?{query}", state


class AppConfig:
    """
    comment
    """

    def __init__(self, config_path: str = "companies.yaml"):
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        shared = raw.get("shared", {})
        if not shared.get("client_id") or not shared.get("client_secret"):
            raise ValueError(
                "client_id and client_secret must be provided in shared config"
            )

        self.companies: dict[str, CompanyConfig] = {}
        for name, data in raw.get("companies", {}).items():
            self.companies[name] = CompanyConfig(name, data or {}, shared)

        if not self.companies:
            raise ValueError("At least one company must be configured")

    def get(self, name: str) -> CompanyConfig:
        """
        comment
        """
        if name not in self.companies:
            raise KeyError(f"Company not found: {name}")
        return self.companies[name]

    @property
    def names(self) -> list[str]:
        """
        comment
        """
        return list(self.companies.keys())
