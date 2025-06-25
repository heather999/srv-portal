FROM python:3.12-slim
#FROM ubuntu:24.04
#ENV DEBIAN_FRONTEND=noninteractive
#RUN apt-get update --quiet -y && \
#    apt-get install -y python3-flask python3-pip
WORKDIR /app
COPY web /app
RUN pip3 install -r requirements.txt 
#
EXPOSE 5000

ENV FLASK_APP=portal/__init__.py

CMD ["flask", "run", "--host=0.0.0.0"]
RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]


