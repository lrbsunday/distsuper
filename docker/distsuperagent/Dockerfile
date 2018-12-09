FROM python:3.7

#RUN sed -i "s@http://deb.debian.org@https://mirrors.aliyun.com@g" /etc/apt/sources.list
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
    echo "[global]\nindex-url=https://pypi.tuna.tsinghua.edu.cn/simple/\n[install]\ntrusted-host=pypi.tuna.tsinghua.edu.cn\n" > ~/.pip/pip.conf
RUN apt-get -y update && \
    apt-get -y install vim

WORKDIR /home/distsuper
RUN mkdir /var/log/distsuperd /var/log/distsuperagent

COPY . .
RUN python setup.py install
COPY distsuper/configure/distsuper.ini /etc/distsuper.ini
RUN chmod +x docker/distsuperagent/entrypoint.sh

EXPOSE 3379

ENTRYPOINT ["./entrypoint.sh"]
CMD [ "distsuperagent", "start" ]