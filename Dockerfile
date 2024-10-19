FROM ubuntu:24.04

WORKDIR /tmp

# Update apt and install git
RUN apt-get update && apt-get upgrade -y && apt-get install -y git

# Pull down latest Binwalk code
RUN git clone https://github.com/ReFirmLabs/binwalk.git

# Allow pip to install packages system-wide
RUN mkdir -p $HOME/.config/pip && echo "[global]" > $HOME/.config/pip/pip.conf && echo "break-system-packages = true" >> $HOME/.config/pip/pip.conf

# Install all system dependencies
RUN /tmp/binwalk/dependencies/ubuntu.sh

# Install Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

# Build and install Binwalk
RUN cd /tmp/binwalk && /root/.cargo/bin/cargo build --release && cp ./target/release/binwalk /usr/local/bin/binwalk

# Clean up binwalk build directory
RUN rm -rf /tmp/binwalk

RUN useradd -m -u 1337 -s /sbin/nologin appuser

WORKDIR /home/appuser

USER appuser

ENTRYPOINT [ "binwalk" ]
