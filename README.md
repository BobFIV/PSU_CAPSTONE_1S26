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
PlantUML source file: [media/msc.puml](media/msc.puml)

![MSC diagram](media/msc.svg)




