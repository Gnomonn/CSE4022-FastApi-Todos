# Dockerfile for JMeter image
FROM ubuntu:22.04

# Set JMeter version and environment variables
ENV JMETER_VERSION=5.4.1
ENV JMETER_HOME=/opt/apache-jmeter-${JMETER_VERSION}
ENV PATH=${JMETER_HOME}/bin:$PATH

# Install required packages (wget, unzip, java)
RUN apt-get update && \
    apt-get install -y wget unzip openjdk-11-jre-headless && \
    rm -rf /var/lib/apt/lists/*

# Download and extract Apache JMeter
RUN wget https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.tgz && \
    tar -xzf apache-jmeter-${JMETER_VERSION}.tgz -C /opt/ && \
    rm apache-jmeter-${JMETER_VERSION}.tgz

# Set the working directory
WORKDIR ${JMETER_HOME}

# Default command: run JMeter in non-GUI mode
CMD ["jmeter", "-n"]
