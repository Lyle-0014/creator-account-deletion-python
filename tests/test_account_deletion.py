from src.account_deletion import AccountState, CaptchaClient, CreatorAccountService, DeleteAccountRequest


def test_deletion_revokes_sessions_and_clears_creator_data():
    def opener(request):
        class Response:
            status = 200

            def read(self):
                return b'{"ok": true, "data": {"verified": true}, "error": null, "metadata": {}}'

        return Response()

    state = AccountState(["asset"], ["sub"], ["job"], ["s1", "s2"])
    result = CreatorAccountService(CaptchaClient(opener=opener)).delete_account(
        DeleteAccountRequest("u1", "captcha", "203.0.113.4"), state
    )
    assert result == {"user_id": "u1", "deleted": True, "sessions_revoked": 2}
    assert state == AccountState(deleted=True)
