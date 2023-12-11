FROM python:3.10-bullseye
COPY req.txt req.txt
RUN python3 -m pip install -r req.txt
COPY . /app
WORKDIR /app
