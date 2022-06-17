##################
Configuration File
##################

The ``debutizer.yaml`` file is Debutizer's source of repository-wide
configuration. Build targets and upload destinations are configured here,
among other things.

If your APT packages are deployed to multiple APT repositories, you should
make a configuration file for each one. If, for example, you had staging and
production repositories, you would create a ``debutizer.stage.yaml`` and
``debutizer.prod.yaml`` file. All commands that consult a configuration file
can be provided the ``--config-file`` flag to tell Debutizer which file to
read from, like this:

..  code-block:: bash

    debutizer build --config-file debutizer.stage.yaml

*********
Reference
*********

distributions
=============

* **Type:** ``array[string]``
* **Required:** Yes

A list of distributions to target during build-time. Distributions are
referenced by their codename, like "focal" or "sid". Any distribution
that's supported by debootstrap can be used here, which is denoted by a
file under ``/usr/share/debootstrap/scripts``. All remotely recent
Ubuntu and Debian versions are supported.

architectures
=============

* **Type:** ``array[string]``
* **Required:** No
* **Default:** Host architecture

..  warning::
    Package cross-building is currently not supported, so this option is
    ignored.

A list of system architectures to target during build-time. Architectures
are referenced using Debian's naming convention, like "amd64" or "arm64".
A table of architecture names can be found under
``/usr/share/dpkg/cputable``.

upstream
========

* **Type:** ``object``
* **Required:** No

Defines an APT repository to use as a read-only cache while building. If a
package that matches the current version is available here, it will not be
built again locally.

This is often the same repository as the one used in the
``target_upstream`` field.

url
---

* **Type:** ``string``
* **Required:** Yes

The URL of the upstream APT repository.

components
----------

* **Type:** ``array[string]``
* **Required:** No
* **Default:** ``["main"]``

The components to include from the APT repository.

is_trusted
----------

* **Type:** ``bool``
* **Required:** No
* **Default:** ``false``

If ``true``, the repository will be used even if the repository's GPG key is
missing or if the repository is unsigned.

gpg_key_url
-----------

* **Type:** ``string``
* **Required:** No

A URL where the GPG key for this repository will be downloaded.

If this value is not supplied, you will get signing errors unless the
``is_trusted`` option is enabled.

upload_target (s3)
==================

* **Type:** ``object``
* **Required:** No

This upload target takes care of uploading artifacts to an S3-compatible
bucket. The bucket may be used as a content source for a static website
through services like CloudFront to create an APT repository.

type
----

* **Type:** ``string``
* **Required:** Yes

Set to "s3".

endpoint
--------

* **Type:** ``string``
* **Required:** Yes

The base URL of the S3-compatible API used by this bucket.

For AWS, this value is ``https://s3.<region>.amazonaws.com``.

For GCP, this value is ``https://storage.googleapis.com``.

bucket
------

* **Type:** ``string``
* **Required:** Yes

The name of the bucket.

prefix
------

* **Type:** ``string``
* **Required:** No

A path prefix to apply to all uploaded resources.

If, for example, this value is set to "ubuntu", object names in
the bucket will be transformed from
``/dists/focal/main/binary-amd64/libcool_1.0.0-1_amd64.deb``
to
``/ubuntu/dists/focal/main/binary-amd64/libcool_1.0.0-1_amd64.deb``.

sign
----

* **Type:** ``bool``
* **Required:** No
* **Default:** ``false``

If ``true``, the repository will be signed using the GPG key specified
by the ``gpg_key_id`` field.

gpg_key_id
----------

* **Type:** ``string``
* **Required:** No

The ID of the GPG key in the keyring to sign the repository with.

cache_control
-------------

* **Type:** ``string``
* **Required:** No
* **Default:** ``public, max-age=3600``

Sets the HTTP ``Cache-Control`` header for artifacts that are being
uploaded to the bucket. Services like CloudFormation will provide this
header to users of your repository when the artifacts are downloaded.

Generally, the default value is fine. If you'd like to disable HTTP
caching, which may be appropriate for a staging bucket where the same
package version can be uploaded multiple times, set this value to
``no-cache``.

Some metadata files, like the ``Release`` file, will always have
caching disabled since they're frequently edited whenever a new
package is introduced.

upload_target (ppa)
===================

* **Type:** ``object``
* **Required:** No

This upload target uploads source packages to a PPA where they will be
built.

type
----

* **Type:** ``string``
* **Required:** Yes

Set to "ppa".

repo
----

* **Type:** ``string``
* **Required:** Yes

The PPA repository name, in the format ``ppa:{author}/{name}``.

sign
----

* **Type:** ``bool``
* **Required:** No
* **Default:** ``true``

If ``true``, the repository will be signed using the GPG key specified
by the ``gpg_key_id`` field. Launchpad requires that files are signed before
being uploaded, so you probably don't want to set this to ``false``.

gpg_key_id
----------

* **Type:** ``string``
* **Required:** No

The ID of the GPG key in the keyring to sign the repository with.

force
-----

* **Type:** ``bool``
* **Required:** No
* **Default:** ``false``

Forces artifact uploading, even if the server thinks the artifacts have already
been uploaded.

package_sources
===============

* **Type:** ``array[object]``
* **Required:** No

A list of objects specifying package sources to include in the build
chroot. This is necessary if your packages have dependencies on other
packages that are in a third-party APT repository.

entry
-----

* **Type:** ``string``
* **Required:** Yes

An APT source entry, like those inside ``/etc/apt/sources.list``. For
example, if you wanted to add Kitware's repository to get newer
versions of CMake, the entry value would look like this:

..  code-block::

    deb https://apt.kitware.com/ubuntu/ focal main

gpg_key_url
-----------

* **Type:** ``string``
* **Required:** No

A URL where the GPG key for this repository will be downloaded.

If this value is not supplied, you will get signing errors unless the
``trusted`` option is enabled in the APT source entry. Doing this
turns off package signature checks and is therefor less secure.

*******
Example
*******

..  code-block:: yaml

    distributions:
      - bionic
      - focal
      - jammy

    upstream:
      url: http://apt.coolcompany.dev
      components: [main]
      gpg_key_url: https://apt.coolcompany.dev/public.key

    package_sources:
      - entry: deb https://apt.repos.intel.com/openvino/2021 all main
        gpg_key_url: https://apt.repos.intel.com/openvino/2021/GPG-PUB-KEY-INTEL-OPENVINO-2021
      - entry: deb https://apt.kitware.com/ubuntu/ focal main
        gpg_key_url: https://apt.kitware.com/keys/kitware-archive-latest.asc

    upload_target:
      type: s3
      endpoint: https://storage.googleapis.com
      bucket: cool-apt-bucket
      sign: true
      gpg_key_id: DEADBEEF
