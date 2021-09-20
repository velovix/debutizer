ARG DISTRIBUTION_NAME
ARG DISTRIBUTION_VERSION
FROM ${DISTRIBUTION_NAME}:${DISTRIBUTION_VERSION}

ARG DISTRIBUTION_ARCHITECTURE
ARG SOURCE_PACKAGE_NAME
ARG UPSTREAM_VERSION
ARG REPOSITORY_URL
ARG REVISION

RUN if [ "${LOCAL_REPO_URL}" != "" ]; then \
    echo "deb [arch=${DISTRIBUTION_ARCHITECTURE}, trusted=yes] ${LOCAL_REPO_URL}/ubuntu bionic main" \
    >> /etc/apt/sources.list.d/local.list; \
    fi

RUN if [ "${REMOTE_REPO_URL}" != "" ]; then \
    echo "deb [arch=${DISTRIBUTION_ARCHITECTURE}, trusted=yes] ${REMOTE_REPO_URL}/ubuntu bionic main" \
    >> /etc/apt/sources.list.d/remote.list; \
    fi


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # Debian packaging tools
        devscripts debhelper fakeroot equivs \
        # For fetching source
        ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN update-ca-certificates && \
    # Clone the repository
    git clone \
    --depth 1 \
    --branch ${REVISION} \
    ${REPOSITORY_URL} \
    /build/${SOURCE_PACKAGE_NAME}-${UPSTREAM_VERSION}

# Remove the Git metadata so it doesn't get packaged
RUN rm -r /build/${SOURCE_PACKAGE_NAME}-${UPSTREAM_VERSION}/.git

# For some reason, apt requires a *.orig.tar.gz file in the previous \
# directory
RUN tar --create --gzip \
    --file ${SOURCE_PACKAGE_NAME}_${UPSTREAM_VERSION}.orig.tar.gz \
    --directory /build/${SOURCE_PACKAGE_NAME}-${UPSTREAM_VERSION} .

WORKDIR /build/${SOURCE_PACKAGE_NAME}-${UPSTREAM_VERSION}
ADD ${SOURCE_PACKAGE_NAME}/debian debian

RUN apt-get update && \
    mk-build-deps --install --remove --tool 'apt-get --yes --no-remove --no-install-recommends'
RUN dpkg-buildpackage -us -uc

WORKDIR /output
RUN cp /build/*.deb .

