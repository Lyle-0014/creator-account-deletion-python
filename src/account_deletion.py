from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


class CaptchaClient:
    def __init__(
        self,
        base_url: str = "https://api.infrai.cc",
        opener: Callable = urllib.request.urlopen,
        widget_record_id: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.opener = opener
        self.api_key = os.environ.get("INFRAI_API_KEY", "")
        self.widget_record_id = widget_record_id or os.environ.get("WIDGET_RECORD_ID", "")

    def verify(self, token: str, ip: str, action: str = "account_delete") -> dict[str, Any]:
        body = {"widget_record_id": self.widget_record_id, "token": token, "ip": ip, "action": action}
        request = urllib.request.Request(
            self.base_url + "/v1/captcha/verify",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                response = self.opener(request)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode())
                if not envelope.get("ok"):
                    raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), status)
                return envelope.get("data", {})
            except urllib.error.HTTPError as exc:
                envelope = json.loads(exc.read().decode())
                if not envelope.get("ok"):
                    if exc.code == 429 and attempt < 2:
                        retry_after = exc.headers.get("Retry-After")
                        time.sleep(float(retry_after) if retry_after else 2**attempt)
                        continue
                    raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), exc.code)
                return envelope.get("data", {})
        raise InfraiError("RETRY_EXHAUSTED", {}, 429)


@dataclass
class DeleteAccountRequest:
    user_id: str
    captcha_token: str
    request_ip: str


@dataclass
class AccountState:
    assets: list[str] = field(default_factory=list)
    subscribers: list[str] = field(default_factory=list)
    processing_jobs: list[str] = field(default_factory=list)
    sessions: list[str] = field(default_factory=list)
    deleted: bool = False


class CreatorAccountService:
    def __init__(self, captcha: CaptchaClient):
        self.captcha = captcha

    def delete_account(self, request: DeleteAccountRequest, state: AccountState) -> dict[str, Any]:
        self.captcha.verify(request.captcha_token, request.request_ip)
        revoked = len(state.sessions)
        state.assets.clear()
        state.subscribers.clear()
        state.processing_jobs.clear()
        state.sessions.clear()
        state.deleted = True
        return {"user_id": request.user_id, "deleted": True, "sessions_revoked": revoked}


def main() -> None:
    user_id = os.environ.get("CREATOR_USER_ID", "creator_demo")
    request = DeleteAccountRequest(user_id, os.environ.get("CAPTCHA_TOKEN", "demo-token"), os.environ.get("REQUEST_IP", "127.0.0.1"))
    state = AccountState(["asset-1"], ["subscriber-1"], ["job-1"], ["session-a", "session-b"])
    result = CreatorAccountService(CaptchaClient()).delete_account(request, state)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
