## Start IN-CSE
~~~sh
docker run -it -p 8080:8080 -e hostIPAddress=localhost -v ./acme_in:/data --name acme-in ankraft/acme-onem2m-cse:latest
~~~
## Start MN1-CSE
~~~sh
docker run -it -p 8081:8080 -e hostIPAddress=localhost -v ./acme_mn1:/data --name acme-mn1 ankraft/acme-onem2m-cse:latest
~~~

## Start MN2-CSE
~~~sh
docker run -it -p 8082:8080 -e hostIPAddress=localhost -v ./acme_mn2:/data --name acme-mn2 ankraft/acme-onem2m-cse:latest
~~~

## Run 
~~~sh
python3 main.py <CSE name> <Container name>
~~~