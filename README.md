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

To reset the DB state

```bash
docker compose down -v
```

You should now have a development hub server available on `http://localhost/` to
play with.\
user is admin and password is admin

## Manual setup

You may need to edit in the conference admin srceen the conference dates (start
and end dates) so that we can create events with dates in this range.

You may need to manually create an Assembly with a slug "cdc".

The Assembly needs to be in a state "registered" then in a state "accepted" ?
(not sure)

You may need to create an API Token for your assembly.

You may need to manually create Rooms in the assembly with Name corresponding
with the ROOM mapping table.

## python env for nixos user

```bash
nix develop
```

## Running the ETL

All the relevant code is in the file _main.py_ All the relevant settings are in
the file _settings.py_ You may need to copy it from settings.py.template

```bash
cp settings.py.template settings.py
```

You may need to read these files and edit the relevant settings.

You may run it as follow

```bash
python3 ./main.py
```

## Common problems

### the api token is not valid

You should be able to test your api token with a simple curl, for example:

```bash
curl -v -H "Authorization: Bearer c3hub_tMzGgU9uz5qYqOQwxvZ75uYJdDrnPsVclI6GVgKeqNY5sEt6T0" -L "http://localhost/api/v2/assemblies/?slug=cdc"
```

It could also be that the assembly is not in the state "accepted" ? (not sure)

### A form is invalid while submitting it

It is usually a problem of schedule_start datetime that should be in the range
of conference start datetime and end datetime.

schedule_start + duration should also belong to this range.

Check the conference start and end datetime.

It can also be a problem if 2 events in the same room have schedule datetime
that intersect.

check the logs.

## Caveats

### Tags field

This code use the event tags field to store the Code from pretalx. It is
recommended to not use this field as it could lead to bugs.

### The Hub is a slave

With the current implementation, the Hub datastore, for the event object, is a
slave of what comes from pretalx. Any changes to events only done in the Hub
will likely be overwritten. Any Events only created in the Hub but not in
pretalx will most likely be deleted.
