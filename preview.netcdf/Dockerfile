FROM ubuntu:20.04

RUN apt-get update &&\
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python-is-python3

# copy requirements file
COPY requirements.txt /home/clowder/
RUN pip3 install -r /home/clowder/requirements.txt

# command to run when starting docker
ENTRYPOINT ["/home/clowder/entrypoint.sh"]
CMD ["extractor"]

# Setup environment variables. These are passed into the container. You can change
# these to your setup. If RABBITMQ_URI is not set, it will try and use the rabbitmq
# server that is linked into the container. MAIN_SCRIPT is set to the script to be
# executed by entrypoint.sh
ENV VERSION=${VERSION} \
    BUILDNUMBER=${BUILDNUMBER} \
    GITSHA1=${GITSHA1} \
    RABBITMQ_URI="" \
    RABBITMQ_EXCHANGE="clowder" \
    RABBITMQ_VHOST="%2F" \
    RABBITMQ_QUEUE="ncsa.geo.netdcdf.extractor" \
    MAIN_SCRIPT="ncsa.geo.netcdf.extractor.py"

# copy rest of the files needed
COPY entrypoint.sh *.py extractor_info.json /home/clowder/