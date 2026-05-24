# AIPPT Authentication

AIPPT uses SJTU jAccount as the production identity provider, matching the
pattern used by `/Users/k/ai/course/aistudy`.

## Routes

```text
GET  /api/auth/jaccount/login?next=/decks
GET  /api/auth/jaccount/callback?code=...&state=...
GET  /api/auth/me
POST /api/auth/logout
GET  /api/auth/logout
```

The legacy password register/login routes still exist for early local testing,
but product UI should use jAccount.

## OAuth Flow

1. `/api/auth/jaccount/login` creates a random OAuth `state`.
2. The state and `next` path are stored in a signed, HttpOnly
   `aippt_oauth_state` cookie.
3. The browser is redirected to `https://jaccount.sjtu.edu.cn/oauth2/authorize`.
4. `/api/auth/jaccount/callback` validates the signed state cookie.
5. The API exchanges `code` for an access token.
6. The API fetches `https://api.sjtu.edu.cn/v1/me/profile`.
7. The user is upserted by `jaccount`.
8. The API writes the normal signed `aippt_session` cookie.

No OAuth token is stored in the database or exposed to the browser.

## User Model

`User.jaccount` is the primary production identity. AIPPT also stores:

- `code`: student/staff number when provided by jAccount.
- `display_name`: profile name, falling back to jAccount.
- `email`: profile email, falling back to `{jaccount}@sjtu.edu.cn`.
- `affiliation`: college/unit from the profile.
- `user_type`: `student`, `faculty`, or other jAccount profile value.
- `last_login_at`: updated on every jAccount login.

## Environment

Register the OAuth application at `https://developer.sjtu.edu.cn/`.

```bash
AIPPT_APP_ENV=production
AIPPT_SESSION_SECRET=...
AIPPT_SECURE_COOKIES=true
AIPPT_JACCOUNT_CLIENT_ID=...
AIPPT_JACCOUNT_CLIENT_SECRET=...
AIPPT_JACCOUNT_REDIRECT_URI=https://your-domain.example/api/auth/jaccount/callback
AIPPT_JACCOUNT_SCOPE=basic
```

For local development, `AIPPT_APP_ENV=development` enables fake jAccount login:

```text
/api/auth/jaccount/login?dev_login=alice&next=/decks
```

Never enable fake login in production.
