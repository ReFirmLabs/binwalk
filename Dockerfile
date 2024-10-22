FROM ubuntu:24.04

ARG BINWALK_INSTALL_DIR="/tmp/binwalk"
ARG DEFAULT_WORKING_DIR="/analysis"

WORKDIR /tmp

# Update apt
RUN apt-get update && apt-get upgrade -y

# Copy over the Binwalk build directory
RUN mkdir -p ${BINWALK_INSTALL_DIR}
COPY . ${BINWALK_INSTALL_DIR}

# Allow pip to install packages system-wide
RUN mkdir -p $HOME/.config/pip && echo "[global]" > $HOME/.config/pip/pip.conf && echo "break-system-packages = true" >> $HOME/.config/pip/pip.conf

# Install all system dependencies
RUN ${BINWALK_INSTALL_DIR}/dependencies/ubuntu.sh

# Install Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

# Build and install Binwalk
RUN cd ${BINWALK_INSTALL_DIR} && /root/.cargo/bin/cargo build --release && cp ./target/release/binwalk /usr/local/bin/binwalk

# Clean up binwalk build directory
RUN rm -rf ${BINWALK_INSTALL_DIR}

# Create the working directory
RUN mkdir -p ${DEFAULT_WORKING_DIR} && chmod 777 ${DEFAULT_WORKING_DIR}
WORKDIR ${DEFAULT_WORKING_DIR}

# Run as the default ubuntu user
USER ubuntu

# Enable this environment variable to remove extractor top-level symlink,
# as the symlink target path in the docker environment will not match that of the host.
ENV BINWALK_RM_EXTRACTION_SYMLINK=1

ENTRYPOINT [ "binwalk" ]
