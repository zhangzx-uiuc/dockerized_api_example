# dockerized_api_example

This is an example of a dockerized API and some detailed on how to build it.

### 1. Write a single Python function that runs your trained model and returns the output. 

The corresponding examples in this repo are [task1_predict](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/8d060619953dfcab452f49b9e4d5c39ac617b399/run.py#L320) and [task2_predict](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/8d060619953dfcab452f49b9e4d5c39ac617b399/run.py#L390) (in schema matching, we need to run on two tasks, usually you only need to do one function). Of course, what you need to do in this function depends on the specific task you model is performing.

### 2. Implement a Python API for your task and test it locally.
You can refer to [server.py](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/8d060619953dfcab452f49b9e4d5c39ac617b399/server.py). I am using Flask but you can use any libraries as long as it works. The API will take the "results" JSON as input, then read the input data, run the model, and finally write the output results by adding a new dict key in "results". In this repo, the two APIs for task1 and task2 are [return_opinions_task1](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/8d060619953dfcab452f49b9e4d5c39ac617b399/server.py#L44) and [return_opinions_task2](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/8d060619953dfcab452f49b9e4d5c39ac617b399/server.py#L61) respectively.

After implementing your API, you need to first test it locally before dockerization, because debugging after dockerization will be much harder. In this repo, you can just run `python server.py -p 2324` (2324 is just a random port number, you can use any available port numbers you like) to start the server. And then run `python request.py` to try whether the API works normally (you need to construct your own request similar to that in [request.py](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/c238953b1e78c7ff028707cef98b65350927fa87/request.py)). You need to implement your own server.py and request.py and make sure it is bug-free.

**[IMPORTANT!] When you implement your API, please make sure to leave the port number as a command line argument** ([how to do it?](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/b8c56e7b82df76cb2ad659d12b44d206129c4929/server.py#L81)). Do not hard-code the port number because we need to re-assign port numbers in the overall pipeline.

### 3. Write a Dockerfile and build the docker image.
After implementing your API and test it in your own Python virtual env, the next step you need to do is wrap-up all dependencies into a docker image. You can refer to the Dockerfile in this repo and in most cases, the only things you need to change is [installing your dependencies](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/5f44406abdfe3d08a9d6eef20540b6111352ae42/Dockerfile#L13) and [copying your files and model checkpoints into the docker](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/5f44406abdfe3d08a9d6eef20540b6111352ae42/Dockerfile#L25).

To build the docker image, you first need to create an account at [DockerHub](https://hub.docker.com/) and create a new repo. Then go to the directory that contains the Dockerfile, and run
```
docker build . -t [USERNAME]/[REPO_NAME]:[TAG_NAME]
```
The `TAG_NAME` is simply defined by yourself to help you on better version controls (the default tag is `latest`).

The first run of the `docker run` command could take a long time (basically it is building a VM from scratch), but it would be much faster after the first run. 

### 4. Run and test the docker container.
After building the docker image successfully, you can use the following command to start your container:
```
docker run -p [PORT_NUMBER]:[PORT_NUMBER] -it [USERNAME]/[REPO_NAME]:[TAG_NAME] /bin/bash
```
The `-p` argument is to enable port mapping inside/outside the container. For the `PORT_NUMBER` here, you can use any port numbers you like, but just make sure that it is consistent with number you will use in `python server.py -p [PORT_NUMBER]`. 
The `-it` argument is to enable the iterative mode running (which makes it easier for debugging). After running this command, you will enter a shell inside the container. Then you can run `python server.py -p [PORT_NUMBER]` again and test it with your `request.py`.

If everything is tested ok, you can push your docker image by
```
docker push [USERNAME]/[REPO_NAME]:[TAG_NAME]
```

### 5. Final Deliveries
(1) The dockerhub link of your docker container.
(2) The `request.py` that shows how to test your API (it also shows the input format of you model).
 


