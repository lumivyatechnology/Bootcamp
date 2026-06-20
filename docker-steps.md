1. Build the images
Backend image
```
docker build -t ai-analyst-backend:v1 -f backend/Dockerfile ./backend
```

Frontend image
```
docker build -t ai-analyst-frontend:v1 -f frontend/Dockerfile ./frontend
```

2. Check if image is created or not
```
docker images
```

3. Login to dockerhub at [Dockerhub](https://hub.docker.com/)
In cli do
```
docker login
```

4. Tag your local image
```
docker tag ai-analyst-backend:v1 anishshilpakar/ai-analyst-backend:v1
docker tag ai-analyst-frontend:v1 anishshilpakar/ai-analyst-frontend:v1
```

5. Push the images to dockerhub registry
```
docker push anishshilpakar/ai-analyst-backend:v1
docker push anishshilpakar/ai-analyst-frontend:v1
```
Now the image should be visible in dockerhub. By default these images will be public so users should be able to pull this image from another machine.
Or it can be used in docker compose file to start necessary app. This way it will auto pull images when containers are created and started

6. Pull the images from dockerhub registry
```
docker pull anishshilpakar/ai-analyst-backend:v1
docker pull anishshilpakar/ai-analyst-frontend:v1
```