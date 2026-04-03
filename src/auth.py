import json
import logging
import time

import requests

from config import CompanyConfig

logger = logging.getLogger(__name__)


class TokenManager:
    """
    comment
    """

    def __init__(self, config: CompanyConfig):
        self.config = config
        self.access_token: str = ""
        self.refresh_token: str = ""
        self.expires_at: float = 0.0

    def save(self, token_dict: dict) -> None:
        with self.config.token_file.open("w", encoding="utf-8") as f:
            json.dump(token_dict, f, ensure_ascii=False, indent=2)
        logger.info("Token saved to file: %s", self.config.token_file)

    def load(self) -> bool:
        if not self.config.token_file.exists():
            logger.warning("Token file not found: %s", self.config.token_file)
            return False
        with self.config.token_file.open(encoding="utf-8") as f:
            data = json.load(f)
        self._apply(data)
        return True

    def _apply(self, token_dict: dict) -> None:
        self.access_token = token_dict["access_token"]
        self.refresh_token = token_dict["refresh_token"]
        self.expires_at = token_dict.get("created_at", time.time()) + token_dict.get(
            "expires_in", 21600
        )

        if "company_id" in token_dict and self.config.company_id == 0:
            self.config.company_id = int(token_dict["company_id"])

    def authorize(self, code: str) -> dict:
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": self.config.redirect_uri,
        }
        resp = requests.post(
            self.config.TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        token_dict = resp.json()
        self._apply(token_dict)
        self.save(token_dict)
        logger.info("Access token obtained successfully")
        return token_dict

    def refresh(self) -> dict:
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": self.refresh_token,
        }
        resp = requests.post(
            self.config.TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        token_dict = resp.json()
        self._apply(token_dict)
        self.save(token_dict)
        logger.info("Refresh token obtained successfully")
        return token_dict

    @property
    def is_expired(self) -> bool:
        """
        comment
        """
        return time.time() >= (self.expires_at - 300)

    def ensure_valid_token(self) -> str:
        """
        comment
        """
        if self.is_expired:
            logger.info("Access token expired, refreshing...")
            self.refresh()
        return self.access_token
