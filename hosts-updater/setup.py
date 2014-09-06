# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
import sys

from setuptools import setup


def main(args):
    setup(
        name="kiji-bento-hosts-updater",
        version="1.0.0",

        # Scripts to install in the bin/ folder and made available on the PATH.
        scripts=[
            "src/main/scripts/bento-update-hosts",
        ],

        # Metadata for upload to PyPI
        author="WibiData",
        author_email="user@kiji.org",
        description="Optional support script for bento-cluster. "
                    "Allows the bento script to edit the /etc/hosts file.",
        license="Apache License 2.0",
        keywords="bento,kijiproject,kiji,hadoop,hbase,cdh,cassandra",
        url="http://www.kiji.org/",
    )


if __name__ == "__main__":
    main(sys.argv)
