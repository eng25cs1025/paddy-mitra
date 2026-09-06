# Deploy Paddy Mitra to the cloud

## Render (recommended)

1. Push this folder to a GitHub repository.
2. In Render, choose **New +** → **Blueprint**.
3. Select the repository and approve `render.yaml`.
4. Wait for the Python build and service to finish.
5. Open the generated `https://...onrender.com` URL.
6. Log in with username `farmer` and the generated `PADDY_PASSWORD` shown in the Render environment settings.

The service uses the host-provided `PORT`, binds to `0.0.0.0`, and exposes `/api/health` for health checks.

The free plan can restart or sleep and does not persist newly registered users between redeploys. For permanent user data, use a paid persistent disk or move users to a database.

## Local run

Use `start-app.ps1` for local Wi-Fi access, or `start-app.ps1 -Public` for a temporary HTTPS tunnel.
