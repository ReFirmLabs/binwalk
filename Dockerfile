# ------------------------------------------------------------------------------------
# Build binwalk
# ------------------------------------------------------------------------------------
FROM rust:bookworm as rust-builder

# Install build dependencies 
RUN apt-get update && apt-get upgrade -y && apt-get install -y libfontconfig1-dev liblzma-dev

WORKDIR /app

COPY ./ ./

RUN cargo build --release

# ------------------------------------------------------------------------------------
# Build C dependencies
# ------------------------------------------------------------------------------------
FROM debian:bookworm AS c-builder

WORKDIR /deps

RUN apt-get update && \
    apt-get install -y build-essential clang liblzo2-dev libucl-dev liblz4-dev git wget unzip zlib1g-dev libbz2-dev

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

# Build LZFSE utility and library
RUN git clone https://github.com/lzfse/lzfse.git && \
    cd lzfse && \
    make install

# Install dmg2img with LZFSE support
RUN git clone https://github.com/Lekensteyn/dmg2img.git && \
    cd dmg2img && \
    make dmg2img HAVE_LZFSE=1

# ------------------------------------------------------------------------------------
# Create the final image from a Python image because some dependencies are Python apps
# ------------------------------------------------------------------------------------
FROM python:3-slim-bookworm as final-install

# Add non-free repository for unrar
RUN sed -i 's/^Components: main$/& contrib non-free/' /etc/apt/sources.list.d/debian.sources

# Install dependencies from official repository
RUN apt-get update && apt-get upgrade -y && apt-get install -y gcc libfontconfig1 liblzo2-2 libucl1 liblz4-1 \
    p7zip-full zstd unzip tar sleuthkit cabextract lz4 lzop device-tree-compiler unrar curl unyaffs git 

# Install python dependencies
RUN pip3 install uefi_firmware jefferson ubi-reader
RUN pip3 install --upgrade lz4 zstandard git+https://github.com/clubby789/python-lzo@b4e39df
RUN pip3 install --upgrade git+https://github.com/marin-m/vmlinux-to-elf

# Install Sasquatch
RUN curl -L -o sasquatch_1.0.deb "https://github.com/onekey-sec/sasquatch/releases/download/sasquatch-v4.5.1-4/sasquatch_1.0_$(dpkg --print-architecture).deb" && \
    dpkg -i sasquatch_1.0.deb && rm sasquatch_1.0.deb

# Take binwalk from the previous image
COPY --from=rust-builder /app/target/release/binwalk /usr/bin/binwalk

# Take C dependencies from the previous image
COPY --from=c-builder /deps/dumpifs/dumpifs /usr/bin/dumpifs
COPY --from=c-builder /deps/srec/srec2bin /usr/bin/srec2bin
COPY --from=c-builder /deps/dmg2img/dmg2img /usr/bin/dmg2img
COPY --from=c-builder /deps/lzfse/build/bin/lzfse /usr/bin/lzfse

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
