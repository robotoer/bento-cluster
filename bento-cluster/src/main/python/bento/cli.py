#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
# (c) Copyright 2014 WibiData, Inc.
"""CLI tool for the bento cluster."""

import argparse
import json
import logging
import sys
import time

import docker
import docker.errors

from bento import cluster


# - CLI Implementations ----------------------------------------------------------------------------


def _get_docker_client(args):
    if args.docker_address is None:
        return None
    else:
        return docker.Client(base_url=args.docker_address, version='1.10')


def _get_bento_system(args):
    return cluster.BentoSystem(docker_client=_get_docker_client(args))


def _get_bento(args):
    output_config_dir = None
    hosts_file = None
    if hasattr(args, 'output_config_dir'):
        output_config_dir = args.output_config_dir
    if hasattr(args, 'hosts_file'):
        hosts_file = args.hosts_file
    return cluster.Bento(
        bento_container=args.bento_name,
        docker_client=_get_docker_client(args),
        client_config_dir=output_config_dir,
        hosts_file_path=hosts_file,
    )


def bento_create(args):
    """Creates a new bento docker container.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    created_bento = _get_bento_system(args).create_bento(
        bento_name=args.bento_name,
        platform_version=args.platform_version,
        update_hosts=(not args.skip_hosts_edit),
        write_client_config=(not args.skip_config_write),
        client_config_dir=args.output_config_dir,
        hosts_file_path=args.hosts_file,
        verbose=True
    )
    logging.info('Bento container %s created.', created_bento.bento_container)


def bento_rm(args):
    """Deletes a bento docker container along with its state.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    _get_bento_system(args).delete_bento(args.bento_name, verbose=True)
    logging.info('Bento container %s removed.', args.bento_name)


def bento_list(args):
    """Lists the created bento instances.

    Lists the bento docker containers by listing containers from the bento docker image on the local
    system.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    listed_bentos = _get_bento_system(args).list_bentos(only_running=(not args.all))
    logging.info('Bentos:')
    for bento_cluster in listed_bentos:
        record = dict(name=bento_cluster.bento_hostname, ip=bento_cluster.bento_ip)
        logging.info('  %s', json.dumps(record, sort_keys=True))


def bento_start(args):
    """Starts a bento instance.

    Runs the bento instance by starting the bento docker container.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    bento_cluster = _get_bento(args)
    if bento_cluster.is_container_running:
        logging.info('Bento container %s already started.', bento_cluster.bento_container)
    else:
        bento_cluster.start(
            update_hosts=(not args.skip_hosts_edit),
            write_client_config=(not args.skip_config_write),
            poll_interval=args.poll_interval,
            timeout_ms=args.timeout,
            verbose=True,
        )
        logging.info('Bento container %s started.', bento_cluster.bento_container)


def bento_stop(args):
    """Stops a bento instance.

    Stops the bento instance by killing the docker container. This will not remove the docker
    container's state.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    bento_cluster = _get_bento(args)
    try:
        if bento_cluster.is_container_running:
            bento_cluster.stop(
                poll_interval=args.poll_interval,
                timeout_ms=args.timeout,
                verbose=True,
            )
            logging.info('Bento container %s stopped.', bento_cluster.bento_container)
        else:
            logging.info('Bento container %s not running.', bento_cluster.bento_container)
    except docker.errors.APIError as ae:
        if 'No such container:' in ae.explanation.decode('utf-8'):
            logging.info('Bento does not exist: %s', args.bento_name)
        else:
            raise


def bento_status(args):
    """Prints the status of a bento instance.

    Reports whether or not the bento docker container is running and whether or not the supervisord
    daemon running in the container has successfully initialized hdfs.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    bento_cluster = _get_bento(args)
    try:
        logging.info(
            'Bento container %s.',
            'started' if bento_cluster.is_container_running else 'stopped',
        )
        logging.info(
            'Bento services %s.',
            'started' if bento_cluster.is_running else 'stopped',
        )
    except docker.errors.APIError as ae:
        if 'No such container' in ae.explanation.decode('utf-8'):
            logging.info('Bento does not exist: %s', args.bento_name)
        else:
            raise


def bento_info(args):
    """Prints the configuration record for the bento docker container.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    bento_cluster = _get_bento(args)

    try:
        logging.info('Bento container info:')
        logging.info(json.dumps(bento_cluster.docker_config, sort_keys=True, indent=2))
    except docker.errors.APIError as ae:
        if 'No such container' in ae.explanation.decode('utf-8'):
            logging.info('Bento does not exist: %s', args.bento_name)
        else:
            raise


def bento_pull(args):
    """Pulls the latest bento docker image from dockerhub.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    _get_bento_system(args).pull_bento(platform_version=args.platform_version, verbose=True)


def bento_ip(args):
    """Prints the ip address of a bento instance.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    try:
        print(_get_bento(args).bento_ip)
    except docker.errors.APIError as ae:
        if 'No such container' in ae.explanation.decode('utf-8'):
            logging.info('Bento does not exist: %s', args.bento_name)
        else:
            raise


def bento_hostname(args):
    """Prints the hostname of a bento instance.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    try:
        print(_get_bento(args).bento_hostname)
    except docker.errors.APIError as ae:
        if 'No such container' in ae.explanation.decode('utf-8'):
            logging.info('Bento does not exist: %s', args.bento_name)
        else:
            raise


def bento_logs(args):
    """Prints the logs of the docker container of a bento instance.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    try:
        print(_get_bento(args).get_log().decode('utf-8'))
    except docker.errors.APIError as ae:
        if 'No such container' in ae.explanation.decode('utf-8'):
            logging.info('Bento does not exist: %s', args.bento_name)
        else:
            raise


def bento_config(args):
    """Updates client configuration and hosts files.

    Args:
        args: Object of arguments passed in from the command-line.
    """
    bento_cluster = _get_bento(args)
    try:
        bento_cluster.write_hadoop_config(args.output_config_dir)
        bento_cluster.update_hosts(args.hosts_file)

        logging.info('Bento client configs written to %s', bento_cluster.client_config_dir)
        logging.info(
            'Bento hostname entry "%s %s" added hosts file',
            bento_cluster.bento_hostname,
            bento_cluster.bento_ip
        )
    except docker.errors.APIError as ae:
        if 'No such container' in ae.explanation.decode('utf-8'):
            logging.info('Bento does not exist: %s', args.bento_name)
        else:
            raise


# - Main Entry Point -------------------------------------------------------------------------------


def _setup_logging(log_level):
    """Initializes the logging system.

    Args:
        log_level: Logging level.
    """
    log_formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(filename)s:%(lineno)s : %(message)s",
    )

    # Override the log date formatter to include the time zone:
    def format_time(record, datefmt=None):
        time_tuple = time.localtime(record.created)
        tz_name = time.tzname[time_tuple.tm_isdst]
        return "%(date_time)s-%(millis)03d-%(tz_name)s" % dict(
            date_time=time.strftime("%Y%m%d-%H%M%S", time_tuple),
            millis=record.msecs,
            tz_name=tz_name,
        )

    log_formatter.formatTime = format_time

    logging.root.handlers.clear()
    logging.root.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level)
    logging.root.addHandler(console_handler)


def main(args):
    """
    Program entry point.

    Args:
        args: Command line arguments.
    """
    argument_parser = argparse.ArgumentParser(prog='bento')

    # Global flags.
    argument_parser.add_argument(
        '-n',
        '--bento-name',
        default='bento',
        help='Specifies the name of the docker bento container.',
    )
    argument_parser.add_argument(
        '--docker-address',
        default=None,
        help='Specifies the address of the docker server to connect to.',
    )

    # Add menu options.
    subparsers = argument_parser.add_subparsers(title='Commands')

    create_parser = subparsers.add_parser('create', help='Create and start a new Bento container.')
    create_parser.add_argument(
        '-p',
        '--platform-version',
        default='cdh5.0.3',
        help='Version of the hadoop/hbase stack to run in the bento cluster.'
    )
    create_parser.add_argument(
        '-e',
        '--skip-hosts-edit',
        default=False,
        help='Do not modify environment for bento hostname resolution.',
        action='store_true',
    )
    create_parser.add_argument(
        '-c',
        '--skip-config-write',
        default=False,
        help='Do not overwrite (or write) hadoop client configuration files.',
        action='store_true',
    )
    create_parser.add_argument(
        '-g',
        '--hosts-file',
        default=None,
        help='Hosts file to add dns entries to.',
    )
    create_parser.add_argument(
        '-o',
        '--output-config-dir',
        default=None,
        help='Directory to write hadoop client configuration files to.',
    )
    create_parser.set_defaults(func=bento_create)
    list_parser = subparsers.add_parser('list', help='List all Bento containers.')
    list_parser.add_argument(
        '-a',
        '--all',
        default=False,
        help='List all running and stopped Bento containers.',
        action='store_true',
    )
    list_parser.set_defaults(func=bento_list)
    info_parser = \
        subparsers.add_parser('info', help='Get the configuration of the Bento container.')
    info_parser.set_defaults(func=bento_info)
    rm_parser = subparsers.add_parser('rm', help='Deletes a Bento container and all data.')
    rm_parser.set_defaults(func=bento_rm)
    start_parser = subparsers.add_parser('start', help='Start a Bento container.')
    start_parser.add_argument(
        '-e',
        '--skip-hosts-edit',
        default=False,
        help='Do not modify environment for bento hostname resolution.',
        action='store_true',
    )
    start_parser.add_argument(
        '-c',
        '--skip-config-write',
        default=False,
        help='Do not overwrite (or write) hadoop client configuration files.',
        action='store_true',
    )
    start_parser.add_argument(
        '-g',
        '--hosts-file',
        default=None,
        help='Hosts file to add dns entries to.',
    )
    start_parser.add_argument(
        '-o',
        '--output-config-dir',
        default=None,
        help='Directory to write hadoop client configuration files to.',
    )
    start_parser.add_argument(
        '--poll-interval',
        default=cluster.DEFAULT_POLL_INTERVAL,
        help='Time in milliseconds to wait between checking if the bento instance has started.',
    )
    start_parser.add_argument(
        '--timeout',
        default=cluster.DEFAULT_TIMEOUT_MS,
        help='Time in milliseconds to wait for the bento instance to start.',
    )
    start_parser.set_defaults(func=bento_start)
    stop_parser = subparsers.add_parser('stop', help='Stop a Bento container.')
    stop_parser.add_argument(
        '--poll-interval',
        default=cluster.DEFAULT_POLL_INTERVAL,
        help='Time in milliseconds to wait between checking if the bento instance has stopped.',
    )
    stop_parser.add_argument(
        '--timeout',
        default=cluster.DEFAULT_TIMEOUT_MS,
        help='Time in milliseconds to wait for the bento instance to stop.',
    )
    stop_parser.set_defaults(func=bento_stop)
    status_parser = \
        subparsers.add_parser('status', help='Gets the status of a running bento container.')
    status_parser.set_defaults(func=bento_status)
    pull_parser = subparsers.add_parser('pull', help='Pull the latest Bento image from docker hub.')
    pull_parser.add_argument(
        '-p',
        '--platform-version',
        default='cdh5.0.3',
        help='Version of the hadoop/hbase stack to run in the bento cluster.'
    )
    pull_parser.set_defaults(func=bento_pull)
    ip_parser = subparsers.add_parser('ip', help='Get the ip address of a Bento container.')
    ip_parser.set_defaults(func=bento_ip)
    hostname_parser = \
        subparsers.add_parser('hostname', help='Get the host name of a Bento container.')
    hostname_parser.set_defaults(func=bento_hostname)
    logs_parser = subparsers.add_parser('logs', help='Tail the Bento process logs.')
    logs_parser.set_defaults(func=bento_logs)
    config_parser = \
        subparsers.add_parser('config', help='Dump config files in specified directory.')
    config_parser.add_argument(
        '-o',
        '--output-config-dir',
        default=None,
        help='Directory to write hadoop client configuration files to.',
    )
    config_parser.add_argument(
        '-g',
        '--hosts-file',
        default=None,
        help='Hosts file to add dns entries to.',
    )
    config_parser.set_defaults(func=bento_config)

    parsed_args = argument_parser.parse_args(args=args)
    if hasattr(parsed_args, 'func'):
        parsed_args.func(parsed_args)
    else:
        argument_parser.print_usage()


if __name__ == '__main__':
    _setup_logging(logging.INFO)

    # Remove the first argument.
    main(sys.argv[1:])
