FROM python:3.7

RUN echo "Asia/Shanghai" > /etc/timezone && export TZ="Asia/Shanghai"
RUN echo " \
    deb http://mirrors.aliyun.com/debian/ stretch main non-free contrib \
    deb http://mirrors.aliyun.com/debian/ stretch-updates main non-free contrib \
    deb http://mirrors.aliyun.com/debian/ stretch-backports main non-free contrib \
    deb-src http://mirrors.aliyun.com/debian/ stretch main non-free contrib \
    deb-src http://mirrors.aliyun.com/debian/ stretch-updates main non-free contrib \
    deb-src http://mirrors.aliyun.com/debian/ stretch-backports main non-free contrib \
    deb http://mirrors.aliyun.com/debian-security/ stretch/updates main non-free contrib \
    deb-src http://mirrors.aliyun.com/debian-security/ stretch/updates main non-free contrib \
    " >  /etc/apt/sources.list
RUN mkdir ~/.pip && \
    echo " \
    [global] \
    index-url=https://pypi.tuna.tsinghua.edu.cn/simple/ \
    [install] \
    trusted-host=pypi.tuna.tsinghua.edu.cn \
    " > ~/.pip/pip.conf
RUN apt-get -y update && \
    apt-get -y install vim

WORKDIR /home/distsuper
RUN mkdir /var/log/distsuperd

COPY . .
RUN python setup.py install
COPY distsuper/configure/distsuper-docker.ini /etc/distsuper.ini
RUN chmod +x docker/distsuperd/entrypoint.sh

EXPOSE 3378

ENTRYPOINT ["docker/distsuperd/entrypoint.sh"]
CMD [ "distsuperd", "start", "-f" ]