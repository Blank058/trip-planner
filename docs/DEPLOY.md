# Deploying: Supabase + Render

The app runs on **Render** (it runs the Flask code) and stores its data in a **Supabase** Postgres database. Both have free tiers. Allow about 15 minutes.

> Dashboard button names below were accurate when written, but both sites change their UI from time to time. If something is named slightly differently, look for the closest match.

## 1. Create the Supabase database

1. Go to https://supabase.com/dashboard and click **New project**.
2. Pick a name (e.g. `trip-planner`), set a **database password** (save it in a password manager, you'll need it in step 4), and choose the region closest to where your Render service will run (e.g. *West EU (Ireland)* or *East US*).
3. Wait a minute or two for the project to finish setting up.
4. Click **Connect** at the top of the project page. Under **Connection String**, choose the **Session pooler** method and copy the URI. It looks like:

   ```
   postgresql://postgres.abcdefghijkl:[YOUR-PASSWORD]@aws-0-eu-west-1.pooler.supabase.com:5432/postgres
   ```

5. Replace `[YOUR-PASSWORD]` with the password from step 2 (remove the square brackets). If the password contains symbols like `@`, `#`, `/` or `%`, URL-encode them (e.g. `@` → `%40`), or reset the password to letters and numbers only under **Project Settings → Database**.

**Why the Session pooler?** Supabase's *direct* connection uses IPv6 only, and Render can't connect over IPv6. The Session pooler works over IPv4, so use that one.

You don't need to create any tables: the app creates them itself the first time it starts. Once it has run, you can see them in Supabase under **Table Editor** (`trip`, `location_option`, `response`, `location_rank`, `available_day`).

### Optional: test against Supabase locally

Put the connection string in your `.env` file as `DATABASE_URL=...`, run `flask --app app run --debug`, create a trip, and check that rows appear in Supabase's Table Editor.

## 2. Deploy on Render

1. Go to https://dashboard.render.com and sign in with GitHub.
2. Click **New → Blueprint**, pick the **Blank058/trip-planner** repo, and confirm. (If the repo isn't listed, click the option to configure the GitHub app and give Render access to it.)
3. Render reads `render.yaml` from the repo and shows a `trip-planner` web service. It asks for the one value it can't generate:
   - **DATABASE_URL**: paste the Supabase connection string from step 1.5.

   `SECRET_KEY` is generated for you, and `PYTHON_VERSION` is set by the file.
4. Click **Apply**. Render installs the requirements and starts the app; the first deploy takes a few minutes. Watch the **Logs** tab: you want a line like `Booting worker with pid`.
5. Open the URL Render shows (like `https://trip-planner-xxxx.onrender.com`), create a test trip, and respond to it from another browser or your phone.

### Doing it by hand instead of the Blueprint

**New → Web Service**, choose the repo, then:

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn "app:create_app()"` |
| Instance type | Free |
| Environment variables | `DATABASE_URL` = Supabase string, `SECRET_KEY` = any long random string, `PYTHON_VERSION` = `3.12.7` |

Generate a secret key with `python -c "import secrets; print(secrets.token_hex(32))"`.

## 3. After it's live

- **Automatic deploys:** every push to `main` redeploys the app.
- **Free tier sleeps:** a free Render service goes to sleep after about 15 minutes with no visitors, and the next visit takes up to a minute to wake it. Upgrade the instance type if that becomes annoying.
- **Free Supabase pauses:** free Supabase projects are paused after a week with no activity. You can restore one from the dashboard; the data is kept.
- **Changing models:** the app only creates tables that don't exist yet. If you add a column to a model later, add it in Supabase's SQL editor too (or add Flask-Migrate).

## What about GitHub Pages?

GitHub Pages only serves static files, so it can't run the Flask app (saving responses and calculating results need a server). Render does that job. If you want, Pages could host a simple info page that links to your Render URL, but the app works fine without it.

## Troubleshooting

| Symptom (in Render logs) | Fix |
|---|---|
| `could not translate host name` or `Network is unreachable` | You used the *direct* connection string. Use the **Session pooler** one. |
| `password authentication failed` | The password in `DATABASE_URL` is wrong or has unencoded symbols. |
| `ModuleNotFoundError` | The build didn't install requirements; check the build command. |
| Share links start with `http://` | Make sure you're opening the `https://` Render URL; the app copies the scheme you visited with. |
