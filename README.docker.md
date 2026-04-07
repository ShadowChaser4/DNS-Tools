# Local Docker services — Redis & Mongo

This project includes a simple docker-compose configuration to run Redis and MongoDB for local development with persistent volumes.

Files:

- [docker-compose.yml](docker-compose.yml)

Start services (detached):

```bash
docker compose up -d
```

Stop and remove containers (preserve volumes):

```bash
docker compose down
```

Stop and remove containers and volumes (delete data):

```bash
docker compose down -v
```

Connection info:

- MongoDB: mongodb://localhost:27017
- Redis: redis://localhost:6379

Notes:

- By default Mongo runs without authentication for local development. To enable auth, set MONGO_INITDB_ROOT_USERNAME and MONGO_INITDB_ROOT_PASSWORD in docker-compose.yml or an env file and recreate volumes.
- Data is persisted in the named Docker volumes `mongo_data` and `redis_data`.
