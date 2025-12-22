# pretalx-hub-etl

## Setup dev environment for the hub api

You may need to clone the hub repository and run it with docker-compose in order
to test the ETL You may need docker (with docker compose script) to run it
locally

```bash
cd ..
git clone https://git.cccv.de/hub/hub.git
cd hub
```

You may need to change some stuffs to make it run locally: change the build
network, comment out some css lines, add an admin password to login. I had to
make the following changes (git diff output)

```git diff
diff --git a/Dockerfile b/Dockerfile
index f47a443d..a3c12068 100644
--- a/Dockerfile
+++ b/Dockerfile
@@ -156,7 +156,7 @@ RUN install -o appuser -g appuser -m 774 /dev/null /data/django.log
 # Copy additional dev dependencies
 COPY --from=build-dev /install/.venv /install/.venv
 # Copy plainui styles
-COPY --from=node-build /app/plainui/static/*.css* /app/plainui/static/
+# COPY --from=node-build /app/plainui/static/*.css* /app/plainui/static/
 ENV PATH="/install/.venv/bin:$PATH"
 
 USER appuser
diff --git a/docker-compose.yml b/docker-compose.yml
index a25e9c93..7da1a173 100644
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@ -4,6 +4,7 @@ services:
     build:
       context: .
       target: "${BUILD_TARGET:-dev}"
+      network: host
     volumes:
       - ./src:/app
       - hubrun:/run/hub/
@@ -11,6 +12,7 @@ services:
       DJANGO_MIGRATE: "${DJANGO_MIGRATE:-yes}"
       DJANGO_INVOKE_FACTORY: "${DJANGO_INVOKE_FACTORY:-anhalter}"
       DATABASE_URL: "postgis://${HUB_DB_USER:-postgres}:${HUB_DB_PASSWORD:-postgres}@${HUB_DB_HOST:-db}:${DB_PORT:-5432}/${HUB_DB:-postgres}"
+      DJANGO_CREATE_ADMIN_PASSWORD: "admin"
       CLIENT_IP_HEADER: "HTTP_X_REAL_IP"
       NUM_WORKERS: 1
       SERVE_ADMIN: true
@@ -51,6 +53,7 @@ services:
     build:
       context: .
       target: nginx
+      network: host
     volumes:
       - hubrun:/run/hub/
     network_mode: service:db
(END)
```

Then build the containers

```bash
docker compose build
```

Then start the relevant services

```bash
docker compose up -d hub
```

You can optionally tail the logs to see what is happening

```bash
docker compose logs -f
```

You should now have a development hub server available on `http://localhost:80/`
to play with.\
user is admin and password is admin

## python env for nixos user

```bash
nix develop
```
