#!/usr/bin/env python3

""""
exchange rates 

""""

import json
import click
import pkg_resources

def fixer(base, target, value, file_path):
    """
    get currency exchange rate from fixer.io in JSON,
    take note that all the rates are stored as EUR as base
    """

    try:
        """
        try to find the json file which contains currency exchange rates
        """
        with open(file_path) as json_file:
            json_rates = json.load(json_file)
    except FileNotFoundError:
        """
        if file not found, 'fixer_sync' will download the latests rates,
        the range of 200-300 is for succesful HTTP code
        """
        if fixer_sync(file_path) in range(200, 300):
            with open(file_path) as json_file:
                json_rates = json.load(json_file)

    try:
        eur_to_target = json_rates['rates'][target]
        eur_to_base = json_rates['rates'][base]
        result = eur_to_target/eur_to_base * value
    except KeyError:
        if base == 'EUR':
            result = json_rates['rates'][target] * value
        elif target == 'EUR':
            result = (1.0/json_rates['rates'][base]) * value
        else:
            result = "KeyError: Invalid curreny"

    return result

def fixer_sync(file_path):
    """
    downloads the rates JSON to the local location,
    'file_path' is the location where the fixer.io rates will the placed,
    returns status_code, if it is 200 then file successfully created
    """
    url = 'http://api.fixer.io/latest'
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_path, 'wb') as json_file:
            json_file.write(response.content)

    return response.status_code
  
def set_default_base(new_base, default_rates_filepath):
    """ set new default base currency """
    with open(default_rates_filepath) as json_file:
        json_data = json.load(json_file)

    json_data['base'] = new_base

    with open(default_rates_filepath, 'w') as json_file:
        json.dump(json_data, json_file)

def set_default_target(new_target, default_rates_filepath):
    """ set new default arget currency """
    with open(default_rates_filepath) as json_file:
        json_data = json.load(json_file)

    json_data['target'] = new_target

    with open(default_rates_filepath, 'w') as json_file:
        json.dump(json_data, json_file)

def get_default_base(default_rates_filepath):
    """ get the currenct default base currency """
    with open(default_rates_filepath) as json_file:
        json_data = json.load(json_file)
    return json_data['base']

def get_default_target(default_rates_filepath):
    """ get the current default target currency """
    with open(default_rates_filepath) as json_file:
        json_data = json.load(json_file)
    return json_data['target']  

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

RATES_FIXER_JSON_FILE = pkg_resources.resource_filename('fixer_rates.json')
DEFAULT_JSON_FILE = pkg_resources.resource_filename('defaults.json')

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--base', '-b', default=get_default_base(DEFAULT_JSON_FILE),
              type=str, show_default=True,
              help='Currency you are converting from.')
@click.option('--target', '-t', default=get_default_target(DEFAULT_JSON_FILE),
              type=str, show_default=True, help='Currency you\'re converting to.')
@click.option('--amount', '-a', default=1.0, type=float, show_default=True,
              help='Amount to convert.')
@click.option('--set_base', '-sb', is_flag=True, default=False,
              help='Set new default base.')
@click.option('--set_target', '-st', is_flag=True, default=False,
              help='Set new default target.')
def cli(ctx, base, target, amount, set_base, set_target):
    """
    Get the latetst currency exchange rates from:

    \b
        - fixer.io
    """

    if ctx.invoked_subcommand is None:
        output = fixer(base, target, amount, RATES_FIXER_JSON_FILE)
        if isinstance(output, float):
            # 2:.2f for two decimal values, manually specified
            output = "{0} {1} = {2:.2f} {3}".format(amount, base, output, target)

        if set_base:
            set_default_base(base, DEFAULT_JSON_FILE)

        if set_target:
            set_default_target(target, DEFAULT_JSON_FILE)

        click.echo(output)

# subcommands

@cli.command()
def currencies():
    """ prints the list of currencies available """
    with open(RATES_FIXER_JSON_FILE) as rates_json_file:
        json_rates = json.load(rates_json_file)
    list_of_currencies = []
    list_of_currencies.append(json_rates['base'])
    for key in json_rates['rates']:
        list_of_currencies.append(key)
    list_of_currencies.sort()
    click.echo(', '.join(list_of_currencies))

@cli.command()
def sync():
    """ download the latest rates """
    if fixer_sync(RATES_FIXER_JSON_FILE) in range(200, 300):
        click.echo("New rates have been saved.")
