FROM nvidia/cuda:12.1.1-base-ubuntu20.04

ARG GROUPID=0
ARG USERID=0
ARG USERNAME=root
ARG HOMEDIR=/root

RUN if [ ${GROUPID} -ne 0 ]; then addgroup --gid ${GROUPID} ${USERNAME}; fi \
  && if [ ${USERID} -ne 0 ]; then adduser --disabled-password --gecos '' --uid ${USERID} --gid ${GROUPID} ${USERNAME}; fi

ARG DEBIAN_FRONTEND=noninteractive

## Switch to specified user to create directories
USER ${USERID}:${GROUPID}

## Switch to root to install dependencies
USER 0:0

## Dependencies
RUN apt update && apt upgrade -q -y
RUN apt update && apt install -q -y cmake git build-essential lsb-release curl gnupg2
RUN apt update && apt install -q -y libboost-all-dev libomp-dev
RUN apt update && apt install -q -y libx11-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev libsparsehash-dev 
RUN apt update && apt install -q -y freeglut3-dev
RUN apt update && apt install -q -y python3 python3-distutils python3-pip
RUN apt update && apt install -q -y libeigen3-dev
RUN apt update && apt install -q -y libsqlite3-dev sqlite3
RUN apt update && apt install -q -y python-is-python3

WORKDIR /home/asrl/

# COPY requirements.txt ./
RUN pip3 install \
    icecream \
    tqdm \
    matplotlib \
    open3d \
    pyyaml \
    tensorboard==2.4.0 \ 
    tensorboardX==2.1 \
    vispy==0.7.0 \
    Cython==0.29.26 \
    easydict==1.9 \
    nose==1.3.7 \
    numpy==1.19.4 \
    opencv-contrib-python==4.5.1.48 \
    opencv-python==4.5.1.48 \
    scikit-learn==0.24.2 \
    strictyaml==1.4.4 \
    torchvision==0.8.0 \
    ipython \
    numba 
RUN pip3 install sparsehash

RUN git clone https://github.com/marijapili/MotionSeg3D.git &&\
    git clone https://github.com/alexandrosstergiou/SoftPool.git &&\
    cd SoftPool &&\
    git checkout 2d2ec6d # rollback to 2d2ec6dca10b7683ffd41061a27910d67816bfa5 &&\
    cd pytorch &&\
    make install

RUN pip3 install --upgrade git+https://github.com/mit-han-lab/torchsparse.git@v1.4.0