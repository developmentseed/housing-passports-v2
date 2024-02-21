
# Runing HP IN DOCKER ENVIRONMENT

In this section, we have the environment work that we need to build the model evaluations and run post-processing:

**Containers**

- `hpnb`: This is used for running the notebooks on the model evaluation.

- `tfs_properties`:  Api service for `developmentseed/building_properties:v1`

- `tfs_parts`: Api service for `developmentseed/building_parts:v1`

- `hpdb` : Postgis database

-  `hpdev`: Cotainer used for upload tthe files into the database.

### Build docker images


```
docker-compose build
```

### Execute DB

```
docker-compose up hpdb
```

### Access to Dev environment

```
docker-compose run hpdev
```

Testing access to DB

```
pg_isready -h hpdb -p 5432 
```