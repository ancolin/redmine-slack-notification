FROM python:3.6.8
COPY requirements /
RUN python -m pip install -r /requirements

WORKDIR /root/work
