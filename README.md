# Quizly API

Backend for Quizly, a service that turns YouTube videos into multiple-choice
quizzes. A user sends a YouTube URL, the API downloads the audio, transcribes it
with Whisper and lets Gemini generate a quiz with 10 questions. The project is a
Django REST Framework API; a client application talks to it over HTTP.

- **Framework:** Django 6.1 with Django REST Framework 3.18
- **Authentication:** JWT (SimpleJWT) stored in `HttpOnly` cookies
- **Database:** PostgreSQL 17, started as a container
- **Quiz generation:** yt-dlp and ffmpeg (audio), Whisper (transcription), Gemini (questions)
- **Runtime:** Python 3.13 inside Docker, served by gunicorn

---

## Table of contents

- [Quick start](#quick-start)
- [Try the API](#try-the-api)
- [Admin panel](#admin-panel)
- [Useful commands](#useful-commands)
- [Configuration](#configuration)
- [Running in production](#running-in-production)
- [Project layout](#project-layout)
- [How a quiz is created](#how-a-quiz-is-created)
- [Authentication](#authentication)
- [Permissions](#permissions)
- [API reference](#api-reference)
- [Tests](#tests)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Quick start

**Requirements:** [Docker](https://docs.docker.com/get-docker/) with Docker
Compose v2 and a [Gemini API key](https://aistudio.google.com/apikey). ffmpeg is
required as well, because Whisper needs it to read the audio. The Docker image
already contains it, so nothing else has to be installed on your machine.

Get the code:

```bash
git clone https://github.com/calvin-kamp/quizly-backend.git
cd quizly-backend
```

Create the `.env` file from the template:

**Windows (PowerShell)**

```powershell
Copy-Item .env.template .env
```

**macOS / Linux**

```bash
cp .env.template .env
```

Open `.env` and replace `YOUR_GEMINI_API_KEY` with your key. All other values of
the template work for local development as they are, see
[Configuration](#configuration).

Build and start the containers:

```bash
docker compose up --build
```

The API is now available at `http://localhost:8000/api/`.

The first build takes a while: the image contains PyTorch, and the Whisper model
(about 460 MB, model `small`) is downloaded during the build, so the first quiz
request does not have to fetch it. Whisper needs about 2 GB of memory while it
transcribes. The migrations are part of the repository and are applied
automatically when the container starts.

`docker compose up` also applies `compose.override.yaml`: it starts Django's
development server with auto-reload, mounts the project folder into the
container and exposes the database on port `5432`.

Every command of this README is run from the project root, the folder that
contains `manage.py`.

---

## Try the API

Start with a registration, log in and create a quiz from a YouTube video. The
login sets the tokens as cookies, so the following requests have to reuse them:
PowerShell keeps them in a session variable, curl in a cookie file. Postman
works as well and stores the cookies by itself.

**Windows (PowerShell)**

Use `Invoke-RestMethod`. The `curl` command of PowerShell is something else and
does not accept the bash examples.

```powershell
# 1. Register
$register = @{
    username           = "demo"
    email              = "demo@example.com"
    password           = "S3cure-Passw0rd!"
    confirmed_password = "S3cure-Passw0rd!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/register/" -Method Post -ContentType "application/json" -Body $register

# 2. Log in; the cookies are stored in $session
$login = @{ username = "demo"; password = "S3cure-Passw0rd!" } | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/login/" -Method Post -ContentType "application/json" -Body $login -SessionVariable session

# 3. Create a quiz (takes a few minutes, the command waits until it is done)
$quiz = @{ url = "https://www.youtube.com/watch?v=vu3xGr-lNVI" } | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://localhost:8000/api/quizzes/" -Method Post -ContentType "application/json" -Body $quiz -WebSession $session -TimeoutSec 900

$result | ConvertTo-Json -Depth 5

# 4. List all quizzes of the user
Invoke-RestMethod -Uri "http://localhost:8000/api/quizzes/" -WebSession $session | ConvertTo-Json -Depth 5
```

**macOS / Linux**

```bash
# 1. Register
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "email": "demo@example.com", "password": "S3cure-Passw0rd!", "confirmed_password": "S3cure-Passw0rd!"}'

# 2. Log in; the cookies are stored in cookies.txt
curl -c cookies.txt -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "S3cure-Passw0rd!"}'

# 3. Create a quiz (takes a few minutes, the command waits until it is done)
curl -b cookies.txt -X POST http://localhost:8000/api/quizzes/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=vu3xGr-lNVI"}'

# 4. List all quizzes of the user
curl -b cookies.txt http://localhost:8000/api/quizzes/
```

Expected response of the registration: `{"detail":"User created successfully!"}`.
The registration only works once per username; use another username for a second
run. The login response contains no tokens, they are only in the cookies. All
endpoints are described in the [API reference](#api-reference).

---

## Admin panel

Create an account for the admin panel:

```bash
docker compose exec api python manage.py createsuperuser
```

The panel is reachable at `http://localhost:8000/admin/`. There you can edit the
users, the quizzes and the single questions of a quiz. New quizzes are created
with the API, see [Try the API](#try-the-api).

---

## Useful commands

```bash
# Follow the logs of the API
docker compose logs -f api

# Run the migrations manually
docker compose exec api python manage.py migrate

# Open a Django shell
docker compose exec api python manage.py shell

# Run the tests
docker compose exec api python manage.py test

# Stop the containers
docker compose down

# Stop the containers and delete the database
docker compose down -v
```

---

## Configuration

All settings are environment variables. They are set in the `.env` file, which
is created from `.env.template` (see [Quick start](#quick-start)). The template
lists every variable with a value that works for local development; the
variables are explained here.

| Variable               | Required | Example                          | Purpose                                                                           |
| ---------------------- | -------- | -------------------------------- | --------------------------------------------------------------------------------- |
| `SECRET_KEY`           | yes      | `k3j...`                         | Django's cryptographic key. No default, the server needs it.                      |
| `DEBUG`                | no       | `True`                           | Debug mode. Defaults to `False`; never enable it in production.                   |
| `ALLOWED_HOSTS`        | no       | `localhost,127.0.0.1`            | Comma-separated hostnames the server answers for. Required when `DEBUG=False`.    |
| `CORS_ALLOWED_ORIGINS` | no       | `http://localhost:5500`          | Comma-separated origins the client may call the API from.                         |
| `CSRF_TRUSTED_ORIGINS` | no       | `https://quizly.example.com`     | Comma-separated trusted origins for CSRF checks.                                  |
| `JWT_SIGNING_KEY`      | no       | `p9x...`                         | Key that signs the tokens. Falls back to `SECRET_KEY`.                            |
| `AUTH_COOKIE_SECURE`   | no       | `False`                          | `True` sends the auth cookies only over HTTPS. Defaults to `True`.                |
| `GEMINI_API_KEY`       | yes      | `AIza...`                        | Key for the Gemini API. The name has to be exactly `GEMINI_API_KEY`.              |
| `POSTGRES_DB`          | yes      | `quizly`                         | Name of the database the `db` container creates.                                  |
| `POSTGRES_USER`        | yes      | `quizly`                         | Database user.                                                                    |
| `POSTGRES_PASSWORD`    | yes      | `choose-a-password`              | Database password.                                                                |
| `DATABASE_URL`         | yes      | `postgres://quizly:pw@db:5432/quizly` | Connection string. The host is `db` inside Docker.                           |

`AUTH_COOKIE_SECURE=False` is needed for local development over plain HTTP.
Browsers do not send `Secure` cookies over HTTP, so with the default `True` every
request after the login answers `401`.

`DATABASE_URL` has to use the host `db` and the same user, password and database
name as the `POSTGRES_*` values. If the password contains special characters such
as `@` or `/`, URL-encode them there or choose a password without them.

`CORS_ALLOWED_ORIGINS` has to contain the exact origin the client is served from,
including protocol and port.

The server will not start without a `SECRET_KEY`.

---

## Running in production

```bash
docker compose -f compose.yaml up -d --build
```

The `-f compose.yaml` flag skips the override file. The container then runs
gunicorn with a request timeout of 600 seconds and collects the static files on
start. Before deploying, set in `.env`:

- `DEBUG=False`
- `AUTH_COOKIE_SECURE=True` and serve the API over HTTPS
- `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` to the real domains
- new random values for `SECRET_KEY` and `JWT_SIGNING_KEY`. The values of the
  template are only meant for development. Generate a random value, once per
  key, with (no local Python needed):

```bash
docker compose run --rm --no-deps --entrypoint python api -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## Project layout

```
core/          Project configuration and root URLs
app_auth/      Registration, login, logout and token refresh
app_quiz/      Quizzes, questions and the quiz generation
```

Both apps have a `tests/` package with the automated tests (see
[Tests](#tests)).

Each app keeps its API layer in a subpackage (`api/`) holding the serializers,
views, permissions and URLs. `app_auth/api/authentication.py` reads the token
from the cookie, `app_auth/utils.py` sets and deletes the auth cookies.
`app_quiz/utils.py` converts YouTube URLs to the standard form, and the models of
`app_quiz` are managed in the admin panel (`app_quiz/admin.py`). `app_quiz/services/` holds the steps of the quiz generation:

```
services/
  youtube.py        Downloads the audio (yt-dlp)
  whisper.py        Transcribes the audio
  gemini.py         Generates the quiz from the transcript
  quiz_creator.py   Runs all steps and saves the quiz
```

Other files in the root: `compose.yaml` and `compose.override.yaml` (services
`db` and `api`), `Dockerfile`, `entrypoint.sh` (runs the migrations and
`collectstatic` on start) and `.env.template`.

---

## How a quiz is created

`POST /api/quizzes/` runs these steps and answers when they are all done:

1. yt-dlp downloads the audio of the video into a temporary folder.
2. Whisper transcribes the audio. ffmpeg is needed to read the audio file.
3. The temporary folder is deleted.
4. Gemini generates a quiz with 10 questions from the transcript. Every question
   has exactly 4 options and one correct answer.
5. The quiz and its questions are saved in one database transaction.

The request stays open while this runs. Depending on the length of the video it
takes from several seconds to a few minutes.

---

## Authentication

Login sets two cookies. There is no `Authorization` header.

| Cookie          | Lifetime   | Purpose                                     |
| --------------- | ---------- | ------------------------------------------- |
| `access_token`  | 15 minutes | Authenticates every protected request.      |
| `refresh_token` | 7 days     | Used to get a new `access_token`.           |

Both cookies are `HttpOnly` and `SameSite=Lax`; `Secure` follows
`AUTH_COOKIE_SECURE`. The client has to send credentials with every request,
otherwise the cookies are neither stored nor sent. With `fetch` this is
`credentials: "include"`.

When the access token has expired, call `POST /api/token/refresh/` and repeat the
request. `POST /api/logout/` invalidates the refresh token and deletes both
cookies.

Four endpoints work without a valid access token: `POST /api/register/`,
`POST /api/login/`, `POST /api/logout/` and `POST /api/token/refresh/` (which
needs the refresh cookie). Everything else answers `401` without a valid access
token.

Postman keeps the cookies after the login. With curl (macOS / Linux), use a
cookie file; for PowerShell see [Try the API](#try-the-api):

```bash
curl -c cookies.txt -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "S3cure-Passw0rd!"}'

curl -b cookies.txt http://localhost:8000/api/quizzes/
```

---

## Permissions

Every quiz belongs to the user who created it.

| Action                        | Owner | Other user |
| ----------------------------- | ----- | ---------- |
| Create a quiz                 | yes   | yes        |
| List quizzes                  | own only | own only |
| Read a quiz                   | yes   | no (`403`) |
| Change title or description   | yes   | no (`403`) |
| Delete a quiz                 | yes   | no (`403`) |

---

## API reference

Base URL: `http://localhost:8000/api/`

All request and response bodies are JSON.

### Authentication

#### `POST /api/register/`

Creates an account. Public.

Request:

```json
{
  "username": "your_username",
  "password": "your_password",
  "confirmed_password": "your_password",
  "email": "your_email@example.com"
}
```

Response `201`:

```json
{ "detail": "User created successfully!" }
```

`400` when the passwords differ, the email is already in use or the password
fails Django's password validators.

#### `POST /api/login/`

Logs in and sets the cookies `access_token` and `refresh_token`. Public.

Request:

```json
{ "username": "your_username", "password": "your_password" }
```

Response `200`:

```json
{
  "detail": "Login successfully!",
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "your_email@example.com"
  }
}
```

`401` for wrong credentials.

#### `POST /api/logout/`

Invalidates the refresh token and deletes both cookies. The request body is `{}`.

Response `200`:

```json
{
  "detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
}
```

The endpoint also answers `200` when no cookies are present, so it is safe to
call at any time.

#### `POST /api/token/refresh/`

Reads the `refresh_token` cookie and sets a new `access_token` cookie. The
request body is `{}`.

Response `200`:

```json
{ "detail": "Token refreshed" }
```

`401` when the refresh token is missing, expired or invalid.

---

### Quizzes

#### `POST /api/quizzes/`

Creates a quiz from a YouTube video. Only URLs of YouTube videos are accepted:
`youtube.com/watch?v=...`, the mobile and short links (`m.youtube.com`,
`youtu.be/...`), links with additional parameters and `shorts`, `embed` or `live`
links. The URL is stored in the standard form
`https://www.youtube.com/watch?v=<id>`, so the client can embed the video with
`video_url` whichever form was sent. See
[How a quiz is created](#how-a-quiz-is-created).

Request:

```json
{ "url": "https://youtu.be/vu3xGr-lNVI" }
```

Response `201`: the quiz with all questions.

```json
{
  "id": 1,
  "title": "Quiz Title",
  "description": "Quiz Description",
  "created_at": "2026-09-29T12:34:56.789Z",
  "updated_at": "2026-09-29T12:34:56.789Z",
  "video_url": "https://www.youtube.com/watch?v=vu3xGr-lNVI",
  "questions": [
    {
      "id": 1,
      "question_title": "Question 1",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A",
      "created_at": "2026-09-29T12:34:56.789Z",
      "updated_at": "2026-09-29T12:34:56.789Z"
    }
  ]
}
```

`400` for an invalid URL, a URL that is not the URL of a YouTube video or a video
that cannot be downloaded. `401` without a token. `500` when the generation fails, for
example because of the Gemini API.

#### `GET /api/quizzes/`

All quizzes of the logged-in user, newest first. Not paginated.

```json
[
  {
    "id": 1,
    "title": "Quiz Title",
    "description": "Quiz Description",
    "created_at": "2026-09-29T12:34:56.789Z",
    "updated_at": "2026-09-29T12:34:56.789Z",
    "video_url": "https://www.youtube.com/watch?v=vu3xGr-lNVI",
    "questions": [
      {
        "id": 1,
        "question_title": "Question 1",
        "question_options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Option A"
      }
    ]
  }
]
```

`401` without a token.

#### `GET /api/quizzes/{id}/`

One quiz. Same shape as a list entry.

`401` without a token, `403` for a quiz of another user, `404` for an unknown id.

#### `PATCH /api/quizzes/{id}/`

Changes the title and the description. Other fields in the body are ignored.

```json
{
  "title": "Partially Updated Title",
  "description": "Partially Updated Description"
}
```

Response `200`: the full quiz. `400` for invalid data, `401` without a token,
`403` for a quiz of another user, `404` for an unknown id.

`PUT` is not supported and answers `405`.

#### `DELETE /api/quizzes/{id}/`

Deletes the quiz and all its questions permanently. Owner only. `204` with an
empty body. `401` without a token, `403` for a quiz of another user, `404` for an
unknown id.

---

## Tests

The tests use Django's test runner and the `APITestCase` of Django REST
Framework. Run them with the stack running (`docker compose up`), because the
tests need the database container:

```bash
docker compose exec api python manage.py test
```

Django creates a separate test database for the run and deletes it afterwards,
so your data is not touched. The download, Whisper and Gemini are replaced in
the tests, so they need no network access, use no Gemini quota and run quickly.

To run only a part, pass a module or a single test:

```bash
# One app
docker compose exec api python manage.py test app_auth

# One file
docker compose exec api python manage.py test app_quiz.tests.test_quiz_detail

# One test
docker compose exec api python manage.py test app_auth.tests.test_login.LoginTests.test_login_sets_auth_cookies
```

| File                                 | Covers                                                                                       |
| ------------------------------------ | -------------------------------------------------------------------------------------------- |
| `app_auth/tests/test_register.py`    | Registration: valid data, hashed password, duplicate username or email, weak password, missing fields |
| `app_auth/tests/test_login.py`       | Login: cookies (set, `HttpOnly`, lifetime), no tokens in the body, wrong or missing credentials, inactive user, access to a protected endpoint |
| `app_auth/tests/test_logout.py`      | Logout: cookies are deleted, the refresh token is blacklisted, works without cookies         |
| `app_auth/tests/test_token_refresh.py` | Token refresh: new access cookie, missing or invalid refresh cookie                        |
| `app_quiz/tests/test_quiz_create.py` | Quiz creation: result and questions, invalid URL, standard video URL, failed download, login required |
| `app_quiz/tests/test_quiz_list.py`   | Quiz list: only the quizzes of the logged-in user                                            |
| `app_quiz/tests/test_quiz_detail.py` | Reading, changing and deleting a quiz, including the owner check (403) and the 404 case      |
| `app_quiz/tests/test_quiz_creator.py`| The quiz pipeline: saved data, cleanup of the audio file, errors leave nothing behind        |
| `app_quiz/tests/test_utils.py`       | Conversion of YouTube URLs (short, mobile, `shorts`, extra parameters) to the standard form |
| `app_quiz/tests/test_admin.py`       | Admin panel: quizzes and questions are listed and can be changed, questions appear on the quiz page |

---

## Troubleshooting

**`django.core.exceptions.ImproperlyConfigured: Set the SECRET_KEY environment
variable`** — the `.env` file is missing or has no `SECRET_KEY`. See
[Quick start](#quick-start).

**The container stops right after the start** — run `docker compose logs api`.
Compare the `.env` with `.env.template` if a variable is missing. If the database
cannot be reached, `DATABASE_URL` has to use the host `db` (not `localhost`) and
match the `POSTGRES_*` values. After changing `POSTGRES_USER` or
`POSTGRES_PASSWORD`, the old database volume still holds the old values; reset it
with `docker compose down -v` (this deletes all data).

**`relation "app_quiz_quiz" does not exist`** — the migrations have not run.
Run `docker compose exec api python manage.py migrate` and check the logs for the
reason they failed at start.

**`Bad Request (400)` on every request, or `DisallowedHost` in the logs** — the
hostname is not in `ALLOWED_HOSTS`. Add it, for example
`ALLOWED_HOSTS=localhost,127.0.0.1`, and restart the containers.

**`401 Unauthorized` on an endpoint that should work** — log in first; without
the cookies every protected endpoint answers `401`. The access token only lives
15 minutes, so call `POST /api/token/refresh/` or log in again. Check that the
`access_token` cookie exists in the client.

**The login works but the cookies are not sent afterwards** — with
`AUTH_COOKIE_SECURE=True` browsers only send the cookies over HTTPS. Set
`AUTH_COOKIE_SECURE=False` for local development and restart the containers.

**The client loads but every request fails** — the origin the client is served
from is not in `CORS_ALLOWED_ORIGINS`. The value has to match protocol, host and
port exactly. The requests also have to send credentials (`credentials:
"include"` with `fetch`), otherwise the cookies are dropped. Client and API
should run on the same site, for example both on `localhost` with different
ports, because the cookies use `SameSite=Lax`.

**Creating a quiz takes very long** — the transcription runs on the CPU and is
slow for long videos. For faster results use a smaller model: in
`app_quiz/services/whisper.py` and in the `Dockerfile` change `small` to `base`.
Smaller models transcribe less accurately; a larger one such as `turbo` is more
accurate but needs about 1.5 GB of download and several GB of memory.

**The request ends with a timeout, or the log shows `Killed` or `WORKER ... was
sent SIGKILL`** — gunicorn stops a request after 600 seconds (`--timeout` in the
`Dockerfile`), so very long videos need a higher value. `Killed` means the
container ran out of memory: give Docker more memory or use a smaller Whisper
model.

**`FileNotFoundError: ... 'ffmpeg'`, or Whisper cannot read the audio** — ffmpeg
is missing in the image. The `Dockerfile` installs it; rebuild with
`docker compose build --no-cache`.

**`400` with `Video could not be downloaded`** — the video is private,
age-restricted, region-locked or removed. YouTube changes often and old yt-dlp
versions stop working: raise the `yt-dlp` version in `requirements.txt` and
rebuild the image. Only single videos are supported; playlists are ignored.

**`500` when creating a quiz** — check `docker compose logs api`. A message like
`API key not valid` or a quota error comes from Gemini: check `GEMINI_API_KEY` in
`.env` (the name has to be exact) and the limits of your Google account. A
`JSONDecodeError` or `KeyError` means Gemini did not return the expected
structure; try again. Very short or silent videos often cause this, because the
transcript contains too little text.

**`Bind for 0.0.0.0:8000 failed: port is already allocated`** — another program
uses the port. Stop it or change the left side of the port mapping, for example
`"8001:8000"`. The same applies to port `5432` in `compose.override.yaml`.

---

## License

MIT, see [LICENSE](LICENSE).