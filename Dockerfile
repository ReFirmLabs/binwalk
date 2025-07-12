## Scratch build stage
FROM ubuntu:25.04 AS build

ARG BUILD_DIR="/tmp"
ARG BINWALK_BUILD_DIR="${BUILD_DIR}/binwalk"
ARG SASQUATCH_FILENAME="sasquatch_1.0.deb"
ARG SASQUATCH_BASE_FILE_URL="https://github.com/onekey-sec/sasquatch/releases/download/sasquatch-v4.5.1-5/"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

COPY . ${BINWALK_BUILD_DIR}
WORKDIR ${BINWALK_BUILD_DIR}

# Pull build needs, build dumpifs, lzfse, dmg2img, vfdecrypt, and binwalk
# Cleaning up our mess here doesn't matter, as anything generated in
# this stage won't make it into the final image unless it's explicitly copied
RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get -y --no-install-recommends install \
    ca-certificates \
    tzdata \
    curl \
    git \
    wget \
    build-essential \
    clang \
    zlib1g \
    zlib1g-dev \
    liblz4-1 \
    libsrecord-dev \
    liblzma-dev \
    liblzo2-dev \
    libucl-dev \
    liblz4-dev \
    libbz2-dev \
    libssl-dev \
    pkg-config \
    && curl -L -o "${SASQUATCH_FILENAME}" "${SASQUATCH_BASE_FILE_URL}\sasquatch_1.0_$(dpkg --print-architecture).deb" \
    && git clone https://github.com/askac/dumpifs.git ${BUILD_DIR}/dumpifs \
    && git clone https://github.com/lzfse/lzfse.git ${BUILD_DIR}/lzfse \
    && git clone https://github.com/Lekensteyn/dmg2img.git ${BUILD_DIR}/dmg2img \
    && rm ${BUILD_DIR}/dumpifs/dumpifs \
    && make -C ${BUILD_DIR}/dumpifs dumpifs \
    && make -C ${BUILD_DIR}/lzfse install \
    && make -C ${BUILD_DIR}/dmg2img dmg2img vfdecrypt HAVE_LZFSE=1 \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && . /root/.cargo/env \
    && cargo build --release


## Prod image build stage
FROM ubuntu:25.04

ARG BUILD_DIR="/tmp"
ARG BINWALK_BUILD_DIR="${BUILD_DIR}/binwalk"
ARG DEFAULT_WORKING_DIR="/analysis"
ARG SASQUATCH_FILENAME="sasquatch_1.0.deb"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_SYSTEM_PYTHON=1 UV_BREAK_SYSTEM_PACKAGES=1

WORKDIR ${BUILD_DIR}

# Copy the build artifacts from the scratch build stage
COPY --from=build ${BINWALK_BUILD_DIR}/${SASQUATCH_FILENAME} ${BUILD_DIR}/${SASQUATCH_FILENAME}
COPY --from=build /usr/local/bin/lzfse ${BUILD_DIR}/dumpifs/dumpifs ${BUILD_DIR}/dmg2img/dmg2img ${BUILD_DIR}/dmg2img/vfdecrypt ${BINWALK_BUILD_DIR}/target/release/binwalk /usr/local/bin/

# Install dependencies, create default working directory, and remove clang & friends.
# clang is needed to build python-lzo and vmlinux-to-elf, but it's not needed
# afterward, so it's safe to remove and reduces the image size by ~400MB.
# Those two packages could be built in the scratch stage and copied over from it,
# but that would require that I untangle the Eldritch Horror that is the
# pip build process, and that's not a particular monster that I'm up to slaying today.
RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get -y install --no-install-recommends \
    ca-certificates \
    tzdata \
    python3 \
    7zip \
    zstd \
    srecord \
    tar \
    unzip \
    sleuthkit \
    cabextract \
    curl \
    wget \
    git \
    lz4 \
    lzop \
    unrar \
    unyaffs \
    zlib1g \
    zlib1g-dev \
    liblz4-1 \
    libsrecord-dev \
    liblzma-dev \
    liblzo2-dev \
    libucl-dev \
    liblz4-dev \
    libbz2-dev \
    libssl-dev \
    libfontconfig1-dev \
    libpython3-dev \
    7zip-standalone \
    cpio \
    device-tree-compiler \
    clang \
    && dpkg -i ${BUILD_DIR}/${SASQUATCH_FILENAME} \
    && rm ${BUILD_DIR}/${SASQUATCH_FILENAME} \
    && CC=clang uv pip install uefi_firmware jefferson ubi-reader git+https://github.com/marin-m/vmlinux-to-elf \
    && uv cache clean \
    && apt-get purge clang -y \
    && apt autoremove -y \
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/* /bin/uv /bin/uvx \
    && mkdir -p ${DEFAULT_WORKING_DIR} \
    && chmod 777 ${DEFAULT_WORKING_DIR}


WORKDIR ${DEFAULT_WORKING_DIR}

# Run as the default ubuntu user
USER ubuntu

# Enable this environment variable to remove extractor top-level symlink,
# as the symlink target path in the docker environment will not match that of the host.
ENV BINWALK_RM_EXTRACTION_SYMLINK=1

ENTRYPOINT [ "binwalk" ]
