#!/usr/bin/env python
import logging
import urllib
import time
import click
import requests
import csv
from pprint import pprint


class ProfilerError(Exception):
    """
    Represents a human-facing exception.
    """
    def __init__(self, message):
        self.message = message


class Config(object):
    """
    Base configuration class.
    """
    def __init__(self):
        self.verbose = False
        self.log_file = ''
        self.log_levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }
        self.log_level = self.log_levels['warning']
        self.app_host = None 
        self.token = None
        self.headers = {}


# Create decorator allowing configuration to be passed between commands.
pass_config = click.make_pass_decorator(Config, ensure=True)
@click.group()
@click.option('--verbose', is_flag=True, help='Show debug.')
@click.option('--app-host',
              prompt=True,
              envvar='PROFILER_APP_HOST',
              type=click.STRING,
              help="App host: 'protocol://address:port'")
@click.option('--token',
              default="",
              envvar='PROFILER_API_TOKEN',
              type=click.STRING,
              help="App access token.")
@click.option('--log-file',
              type=click.Path(),
              default='',
              help='Log file.')
@click.option('--log-level',
              type=click.Choice(['debug', 'info', 'warning', 'error', 'critical']),
              default='warning',
              help='Log level.')
@pass_config
def cli(config, verbose, app_host, token, log_file, log_level):
    """
    \b
    HGProfiler API Client 
    ----------------------------

    Command line client for interacting with the HGProfiler API.
    """
    config.verbose = verbose

    if not config.verbose:
        requests.packages.urllib3.disable_warnings()

    config.token = token

    if not config.token:
        click.secho('You are not authenticated.', fg='red')

    else:
        click.secho('You are authenticated. X-Auth headers set.', fg='green')
        config.headers['X-Auth'] = config.token

    if app_host:
        config.app_host = app_host

    config.log_file = log_file
    config.log_level = config.log_levels[log_level]

    if config.log_file:
        logging.basicConfig(filename=config.log_file,
			    level=config.log_level,
			    format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=config.log_level,
			    format='%(asctime)s - %(levelname)s - %(message)s')


@cli.command()
@pass_config
@click.option('--username', type=click.STRING, prompt=True, required=True)
@click.option('--password', type=click.STRING, prompt=True, required=True)
def get_token(config, username, password):
    """
    Obtain an API token.
    """
    auth_url = config.app_host + '/api/authentication/'
    payload = {'email': username, 'password': password}
    response = requests.post(auth_url, json=payload, verify=False)
    response.raise_for_status()

    try:
        token = response.json()['token']
    except KeyError:
        raise ProfilerError('Authentication failed.')

    click.secho(token, fg='green')


@cli.command()
@click.argument('input-file', 
                type=click.File(),
                required=True)
@click.option('--group-id', 
                type=click.INT,
                required=False)
@click.option('--chunk-size', 
                type=click.INT,
                required=False,
                default=100)
@click.option('--interval', 
                type=click.INT,
                required=False,
                default=60)
@pass_config
def submit_usernames(config,
                    input_file,
                    group_id,
                    chunk_size,
                    interval):
    """
    Submit list of usernames to search for.

    :param usernames (list): list of usernames to search for.
    :param group_id (int): id of site group to use.
    :param chunk_size (int): usernames to sumbit per API requests.
    :param interval (int): interval in seconds between API requests.
    """
    if not config.token:
        raise ProfilerError('Token is required for this function.')

    reader = csv.reader(input_file)
    usernames = [item[0] for item in list(reader)]

    if not usernames:
        raise ProfilerError('No usernames found.')
    else:
        click.echo('[*] Extracted {} usernames.'.format(len(usernames)))

    username_url = config.app_host + '/api/username/'
    responses = []
    
    with click.progressbar(length=len(usernames),
                           label='Submitting usernames: ') as bar:
        for chunk_start in range(0, len(usernames), chunk_size):
            chunk_end = chunk_start + chunk_size
            chunk = usernames[chunk_start:chunk_end]
            bar.update(len(chunk))
            payload = {
                'usernames': chunk,
            }
            response = requests.post(username_url,
                                     headers=config.headers,
                                     json=payload,
                                     verify=False)
            response.raise_for_status()
            responses.append(response.content)
            time.sleep(interval)

    click.secho('Submitted {} usernames.'.format(len(usernames)), fg='green')
    pprint(responses)


@cli.command()
@pass_config
@click.argument('resource',
              type=click.STRING,
              required=True)
@click.option('--pretty',
              is_flag=True,
              help='Pretty print output.')
def get(config, resource, pretty):
    """
    Fetch JSON from resource.

    Example: /api/workers/
    """
    if not config.token:
        raise ProfilerError('"--token" is required for this function.')

    url = urllib.parse.urljoin(config.app_host, resource)
    response = requests.get(url, headers=config.headers, verify=False)
    response.raise_for_status()

    try:
        if pretty:
            return pprint(response.json())
        else:
            return click.echo(response.json())
    except Exception as e:
        raise


if __name__ == '__main__':
   cli()

