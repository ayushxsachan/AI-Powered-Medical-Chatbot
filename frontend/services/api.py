import os
from typing import Any

import requests


class ApiClient:
    def __init__(self, token: str | None = None):
        self.base_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
        self.token = token

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, **kwargs) -> Any:
        headers = kwargs.pop("headers", self.headers)
        response = requests.request(method, f"{self.base_url}{path}", headers=headers, timeout=90, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise RuntimeError(detail)
        if response.status_code == 204:
            return None
        return response.json()

    def register(self, email: str, password: str, full_name: str | None) -> dict:
        return self._request("POST", "/auth/register", json={"email": email, "password": password, "full_name": full_name})

    def login(self, email: str, password: str) -> dict:
        return self._request("POST", "/auth/login", json={"email": email, "password": password})

    def threads(self, search: str | None = None) -> list[dict]:
        params = {"search": search} if search else {}
        return self._request("GET", "/threads", params=params).get("results", [])

    def create_thread(self, title: str) -> dict:
        return self._request("POST", "/thread/create", json={"title": title})

    def get_thread(self, thread_id: str) -> dict:
        return self._request("GET", f"/thread/{thread_id}")

    def rename_thread(self, thread_id: str, title: str) -> dict:
        return self._request("PUT", f"/thread/{thread_id}", json={"title": title})

    def delete_thread(self, thread_id: str) -> None:
        return self._request("DELETE", f"/thread/{thread_id}")

    def chat(self, message: str, thread_id: str | None, model: str | None = None) -> dict:
        return self._request("POST", "/chat", json={"message": message, "thread_id": thread_id, "model": model})

    def health_profile(self) -> dict:
        return self._request("GET", "/health-profile")

    def update_health_profile(self, payload: dict) -> dict:
        return self._request("PUT", "/health-profile", json=payload)

    def documents(self) -> list[dict]:
        return self._request("GET", "/documents").get("documents", [])

    def upload_document(self, file) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        files = {"file": (file.name, file.getvalue(), file.type or "application/octet-stream")}
        return self._request("POST", "/upload-document", headers=headers, files=files)

    def audit_logs(self) -> list[dict]:
        return self._request("GET", "/audit-logs")
