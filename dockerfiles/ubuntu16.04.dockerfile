FROM ubuntu:16.04

RUN echo "\ 
    deb http://mirrors.aliyun.com/ubuntu/ xenial main multiverse restricted universe \
    deb http://mirrors.aliyun.com/ubuntu/ xenial-backports main multiverse restricted universe \
    deb http://mirrors.aliyun.com/ubuntu/ xenial-proposed main multiverse restricted universe \
    deb http://mirrors.aliyun.com/ubuntu/ xenial-security main multiverse restricted universe \
    deb http://mirrors.aliyun.com/ubuntu/ xenial-updates main multiverse restricted universe" > /etc/apt/sources.list
RUN apt-get update

CMD [ "bash", "/root/main.sh" ]