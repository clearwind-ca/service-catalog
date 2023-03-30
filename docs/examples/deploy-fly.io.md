Fly.io is a service that can deploy Docker containers. For more information on Fly.io, visit [their website](https://fly.io). You'll need to create a Fly.io account to be able to deploy services.

## Installing on Fly.io

You'll need a `fly.toml` file. The command `fly launch` will generate a file for you, but it will end up looking something like this:

```toml
app = "service-catalog"
kill_signal = "SIGINT"
kill_timeout = 5
processes = []

[env]
  PORT = "8000"

[experimental]
  auto_rollback = true

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []
  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"

[[statics]]
  guest_path = "/app/public"
  url_prefix = "/static/"
```

Then deploy the service using `fly launch`.

You'll need to connect to a database and you can do this by running a Postgres container. Documentation on [this is here](https://fly.io/docs/postgres/). Once you've got a Postgres container, you'll need to ssh into that container and create a database.

```bash
fly postgres connect -a YOUR-POSTGRES-APP
```

This will open the postgres console. Then:

```psql
create database catalog;
create user catalog_user with encrypted password 'YOUR-PASSWORD-HERE';
grant all privileges on database catalog to catalog_user;
```

Then quit out of the postgres console and connect up your database like this:

```bash
DATABASE_URL="postgres://catalog_user:YOUR-PASSWORD-HERE@YOUR-POSTGRES-APP.internal/catalog"
```

That's it. You should now be able to do a new deploy using `fly launch` and view your service catalog instance.