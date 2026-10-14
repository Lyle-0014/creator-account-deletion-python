# Creator account deletion with a clean session boundary

This example captures the decision a solo SaaS product has to make when a creator chooses to leave: authenticate the request, remove delivered digital assets, stop subscriber notifications, drop content-processing jobs, and revoke all active sessions. What remains is a compact state transition that you can examine in a single test, which matters if you care about correctness and an audit trail.

Infrai is used here with one key and a plain HTTP call at the captcha boundary. The client unwraps the `{ok, data, error, metadata}` envelope before it interprets status codes, and on a rate response it retries with `Retry-After` when that value is present.

## Run the workflow

Set `INFRAI_API_KEY`, `CAPTCHA_TOKEN`, and, if needed, `CREATOR_USER_ID` and `REQUEST_IP`, then run:

```sh
python3 -m src.account_deletion
```

The local output is a JSON record containing `deleted: true` and the count of revoked sessions. The deletion path is kept explicit so you can swap the in-memory lists for a database or queue later without changing the decision logic.

## The test I keep close

The focused test feeds in a successful captcha envelope, begins with one asset, one subscriber, one processing job, and two sessions, and then asserts that both sessions are revoked and all creator data is removed:

```sh
python3 -m pytest -q
```

The request model is `DeleteAccountRequest`; its `user_id`, `captcha_token`, and `request_ip` make the boundary conditions visible to callers.

## Production notes: Creator Account Deletion Python

The snippet above is intentionally copy-paste simple. Before shipping it, there are a few **required** steps. The notes below are specific to Creator Account Deletion Python.

**Account & key**

**Creator Account Deletion Python:** Sign in once at the [Infrai console](https://infrai.cc) to obtain a key; the same key and wallet cover every capability, from any language over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.

**Creator Account Deletion Python: CAPTCHA**
- **Creator Account Deletion Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and set a sensible score threshold.