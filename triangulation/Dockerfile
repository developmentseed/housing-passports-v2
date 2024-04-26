FROM ghcr.io/osgeo/gdal:ubuntu-full-3.8.3

# Set up Python3 environment
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-setuptools \
    libpython3.8 \
    python3-pip \
    libspatialindex-dev \
    wget \
    ca-certificates \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install requirements
WORKDIR /build
COPY requirements*.txt /build/
RUN pip3 install -r requirements.txt
RUN pip3 install -r requirements-dev.txt

# Install PostgreSQL client and additional tools
RUN apt-get update && apt-get install -y \
    gnupg2 \
    postgresql-client-14 \
    zip \
    unzip \
    vim \
    nano

RUN pip3 install awscli

# Install project requirements
RUN mkdir /build/housing_passports
COPY housing_passports /build/housing_passports
COPY setup.py /build/
RUN python setup.py install

# Set up working directory
WORKDIR /mnt/data
