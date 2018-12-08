FROM python:3

WORKDIR /usr/src/app

#RUN pip install --no-cache-dir distsuper
RUN easy_install dist/distsuper-*.tar.gz

COPY distsuper.ini /etc/distsuper.ini

CMD [ "distsuperd" ]