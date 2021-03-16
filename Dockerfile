FROM python:3-buster AS build-and-install

ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/src/app/bin \
    DEBIAN_FRONTEND=noninteractive

COPY . /tmp
WORKDIR /tmp

### Took out the deps.sh from binwalk's installation script, baked in the dependencies into the main prereqs installation
### The prereqs that dont come from system's repo, are taken care of later
RUN set -xue \
    && apt-get update -qy \
    && apt-get -t buster dist-upgrade -yq --no-install-recommends -o Dpkg::Options::="--force-confold" \
    && ./deps.sh --yes \
    && python3 setup.py install && binwalk -h > /dev/null \
    && apt-get -yq purge *-dev git build-essential gcc g++ \
    && apt-get -y autoremove \
    && apt-get -y autoclean \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "LANG=en_US.UTF-8" >> /etc/default/locale \
    && echo "LANGUAGE=en_US:en" >> /etc/default/locale \
    && echo "LC_ALL=en_US.UTF-8" >> /etc/default/locale \
    && locale-gen

FROM build-and-install AS unit-tests
RUN pip install coverage nose \
    && python3 setup.py test \
    && dd if=/dev/urandom of=/tmp/random.bin bs=1M count=1 && binwalk -J -E /tmp/random.bin

FROM build-and-install AS cleanup-and-release
RUN useradd -m -u 1000 -s /sbin/nologin appuser \
    && rm -rf -- \
        /var/lib/apt/lists/* \
        /tmp/* /var/tmp/* \
        /root/.cache/pip

# Setup locale. This prevents Python 3 IO encoding issues.
ENV DEBIAN_FRONTEND=teletype \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    PYTHONUTF8="1" \
    PYTHONHASHSEED="random"

WORKDIR /home/appuser
USER appuser

ENTRYPOINT ["binwalk"]
