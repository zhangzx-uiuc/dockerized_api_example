# dockerized_api_example

This is an example of a dockerized API and some detailed instructions on how to build it.

### 1. Write a single Python function that runs your trained model and returns the output. 

The corresponding examples in this repo is [task1_predict](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/8d060619953dfcab452f49b9e4d5c39ac617b399/run.py#L320) and [task2_predict](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/8d060619953dfcab452f49b9e4d5c39ac617b399/run.py#L390) (because in schema matching, we need to run on two tasks, usually you only need to do one function). What you need to do in this function depends on the specific task you model is performing.

### 2. Implement a Python API for your task.
You can refer to [server.py](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/8d060619953dfcab452f49b9e4d5c39ac617b399/server.py). I am using Flask, but of course you can use any libraries as long as it works. The API will take the "results" JSON as input, then read the input data, run the model, and finally write the output results by adding a new dict key in "results". In this repo, the two APIs for task1 and task2 are [return_opinions_task1](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/8d060619953dfcab452f49b9e4d5c39ac617b399/server.py#L44) and [return_opinions_task2](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/8d060619953dfcab452f49b9e4d5c39ac617b399/server.py#L61) respectively.

**After implementing your API, please first test it locally before dockerization because debugging after dockerization will be much harder.** In this repo, you can just run `python server.py -p 2324` (2324 is just a random port number, you can use any available port numbers you like) to start the server. And then run `python request.py` to try whether the API works normally (you need to construct your own request similar in [request.py](https://github.com/zhangzx-uiuc/dockerized_api_example/blob/c238953b1e78c7ff028707cef98b65350927fa87/request.py)).
