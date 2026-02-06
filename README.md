# PSU_CAPSTONE_1S26
oneM2M Orchestrator

## Running CSEs
- Mount and start IN-CSE
~~~sh
docker run -it -p 8080:8080 -e hostIPAddress=localhost -v ./acme_in:/data --name acme-in ankraft/acme-onem2m-cse:latest
~~~


- Check for running container
~~~sh
docker ps
~~~

## MSC
participant GA as GatewayAgent
participant IN as IN-CSE (ACME)
participant MN as MN-CSE (ACME)
participant CB as Callback Server

1. Start MN-CSE
    - ACME on :8080, mapped to host :8080
2. Gateway Agent reads config
    - MN-CSE base URL: http://localhost:8080
    - originator: Sgateway
    - notification URL: http://host.docker.internal:9999
3. Start callback server on :9999
4. AE registration
    - GA $\to$ MN: CREATE AE
    - MN $\to$ GA: 201 Created
5. Container Setup
    - GA $\to$ MN: CREATE cmd, data
    - MN $\to$ GA: 201 Created
6. Subscription Setup
    - GA $\to$ MN: CREATE sub
    - MN $\to$ GA: 201 Created



