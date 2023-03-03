FROM nvidia/cuda:10.2-base-ubuntu16.04
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH
# Install base packages.
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Chicago
RUN apt-get update --fix-missing && apt-get install -y tzdata && apt-get install -y bzip2 ca-certificates curl gcc git libc-dev libglib2.0-0 libsm6 libxext6 libxrender1 wget libevent-dev build-essential &&  rm -rf /var/lib/apt/lists/*
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc
RUN /opt/conda/bin/conda update -n base -c defaults conda && \
    /opt/conda/bin/conda install pip && \
    /opt/conda/bin/pip install tqdm && \
    /opt/conda/bin/pip install flask && \
    /opt/conda/bin/pip install flask-cors && \
    /opt/conda/bin/pip install tornado && \
    /opt/conda/bin/pip install nltk && \
    /opt/conda/bin/pip install numpy && \
    /opt/conda/bin/pip install lxml && \
    /opt/conda/bin/pip install bs4 && \
    /opt/conda/bin/pip install networkx==2.5.1 

COPY ./schema.py ./ie_graph.py ./matching_events.py ./matching_graphs.py ./prediction.py ./read_xpo_json.py ./run.py ./server.py ./utils.py ./write_sdf.py ./visualization.py ./event_temporal.py ./human_graph.py ./xpo_v4.json /
ADD ./schemas_qz9 /schemas_qz9

LABEL maintainer="zixuan11@illinois.edu"
