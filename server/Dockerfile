FROM debian:11
ENV TZ="Europe/Moscow"
RUN apt-get update -y
RUN apt-get install -y python3 python3-pip
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["./run.sh"]
