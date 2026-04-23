## Start IN-CSE
~~~sh
docker run -it -p 8080:8080 -e hostIPAddress=acme-in -v ./acme_in:/data --name acme-in --network acme-net ankraft/acme-onem2m-cse:latest
~~~
## Start GatewayAgent1
~~~sh
docker run -it --name gateway-app1 --network acme-net --env-file .env.rpi1 -p 9000:9000 -v /var/run/docker.sock:/var/run/docker.sock -v /Users/kimminseo/Documents/CMPSC483W/PSU_CAPSTONE_1S26/cse-data:/shared-cse gateway-app:latest
~~~

## Start GatewayAgent2
~~~sh
docker run -it --name gateway-app2 --network acme-net --env-file .env.rpi2 -p 9001:9000 -v /var/run/docker.sock:/var/run/docker.sock -v /Users/kimminseo/Documents/CMPSC483W/PSU_CAPSTONE_1S26/cse-data:/shared-cse gateway-app:latest
~~~

## Build Image
~~~sh
docker build -t gateway-app:latest .
~~~

## Run 
~~~sh
python3 main.py <CSE name> <Container name>
~~~