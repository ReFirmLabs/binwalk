# ------------------------------------------------------------------------------------
# Build binwalk
# ------------------------------------------------------------------------------------
FROM rust:bookworm as rust-builder

# Install build dependencies 
RUN apt-get update && apt-get upgrade -y && apt-get install -y libfontconfig1-dev

WORKDIR /app

COPY ./ ./

RUN cargo build --release

# ------------------------------------------------------------------------------------
# Build C dependencies
# ------------------------------------------------------------------------------------
FROM debian:bookworm AS c-builder

WORKDIR /deps

RUN apt-get update && \
    apt-get install -y build-essential clang liblzo2-dev libucl-dev liblz4-dev git wget unzip

# Build dumpifs
RUN git clone https://github.com/askac/dumpifs.git dumpifs && \
    cd dumpifs && \
    make dumpifs

# Build srec
RUN mkdir srec && \
    cd srec && \
    wget http://www.goffart.co.uk/s-record/download/srec_151_src.zip && \
    unzip srec_151_src.zip && \
    make

# ------------------------------------------------------------------------------------
# Create the final image from a Python image because some dependencies are Python apps
# ------------------------------------------------------------------------------------
FROM python:3-slim-bookworm as final-install

# Add non-free repository for unrar
RUN sed -i 's/^Components: main$/& contrib non-free/' /etc/apt/sources.list.d/debian.sources

# Install dependencies from official repository
RUN apt-get update && apt-get upgrade -y && apt-get install -y gcc libfontconfig1 liblzo2-2 libucl1 liblz4-1 \
    p7zip-full zstd unzip tar sleuthkit cabextract lz4 lzop device-tree-compiler unrar curl

# Install python dependencies
RUN pip3 install uefi_firmware jefferson ubi-reader

# Install Sasquatch
RUN curl -L -o sasquatch_1.0.deb "https://github.com/onekey-sec/sasquatch/releases/download/sasquatch-v4.5.1-4/sasquatch_1.0_$(dpkg --print-architecture).deb" && \
    dpkg -i sasquatch_1.0.deb && rm sasquatch_1.0.deb

# Take binwalk from the previous image
COPY --from=rust-builder /app/target/release/binwalk /usr/bin/binwalk

# Take C dependencies from the previous image
COPY --from=c-builder /deps/dumpifs/dumpifs /usr/bin/dumpifs
COPY --from=c-builder /deps/srec/srec2bin /usr/bin/srec2bin

# ------------------------------------------------------------------------------------
# Release image
# ------------------------------------------------------------------------------------
FROM final-install as cleanup-and-release

RUN useradd -m -u 1000 -s /sbin/nologin appuser \
    && apt-get -yq purge *-dev git build-essential gcc g++ curl \
    && apt-get -y autoremove \
    && apt-get -y autoclean \
    && rm -rf -- \
        /var/lib/apt/lists/* \
        /tmp/* /var/tmp/* \
        /root/.cache/pip

WORKDIR /home/appuser
USER appuser

ENTRYPOINT [ "binwalk" ]
