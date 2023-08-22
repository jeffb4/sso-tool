"""sso.sso.getcreds - module for getting credentials from AWS SSO."""
import configparser
import time
from datetime import datetime, timedelta
from pathlib import Path

import boto3
import botocore
from dateutil.tz import tzutc

_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"


def request_new_sso_token(environment: str, region: str, start_url: str) -> dict:
    """
    Request a new AWS SSO token from API.
    """
    sso_client = boto3.client("sso-oidc", region_name=region)
    register_res = sso_client.register_client(
        clientName="sso_getcreds",
        clientType="public",
    )
    client_id = register_res["clientId"]
    client_secret = register_res["clientSecret"]
    device_res = sso_client.start_device_authorization(
        clientId=client_id,
        clientSecret=client_secret,
        startUrl=start_url,
    )
    print(f"Open (in browser): {device_res['verificationUriComplete']} (Environment: {environment})")
    print("Waiting", end="", flush=True)
    verification_end_time = datetime.now(tzutc()) + timedelta(seconds=device_res["expiresIn"])

    while datetime.now(tzutc()) < verification_end_time:
        try:
            response = sso_client.create_token(
                grantType=_GRANT_TYPE,
                clientId=client_id,
                clientSecret=client_secret,
                deviceCode=device_res["deviceCode"],
            )
            expires_in = timedelta(seconds=response["expiresIn"])
            token = {
                "startUrl": start_url,
                "region": region,
                "accessToken": response["accessToken"],
                "expiresAt": datetime.now(tzutc()) + expires_in,
            }
            print("success!", flush=True)
            return token
        except sso_client.exceptions.SlowDownException:
            print(f"interval {device_res['interval']}s too short increasing by 5s")
            device_res["interval"] += 5
        except sso_client.exceptions.AuthorizationPendingException:
            print(".", end="", flush=True)
        time.sleep(device_res["interval"])
    return {}


def confirm_aws_directory():
    """
    Confirm that ~/.aws exists, if not create it. Raises errors if unable to
    create the directory, or ~/.aws exists and is not a directory.
    """
    aws_directory = Path("~/.aws").expanduser()
    if not aws_directory.exists():
        Path.mkdir(aws_directory)
    if not aws_directory.is_dir():
        raise ValueError("~/.aws exists and is not directory")


def read_credentials_file() -> configparser.ConfigParser:
    """
    Read and return the ~/.aws/credentials file.
    """
    confirm_aws_directory()
    credentials_path = Path("~/.aws/credentials").expanduser()
    credentials_config = configparser.ConfigParser()
    # Make the config parser case-sensitive
    credentials_config.optionxform = lambda option: option  # type: ignore
    credentials_config.read(credentials_path)
    return credentials_config


def write_credentials_file(config: configparser.ConfigParser):
    """
    Write out a copy of ~/.aws/credentials.
    """
    confirm_aws_directory()
    credentials_path = Path("~/.aws/credentials").expanduser()
    with open(credentials_path, "w") as credentials_file:
        config.write(credentials_file)


def read_config_file() -> configparser.ConfigParser:
    """
    Read and return the ~/.aws/config file.
    """
    confirm_aws_directory()
    config_path = Path("~/.aws/config").expanduser()
    config_config = configparser.ConfigParser()
    # Make the config parser case-sensitive
    config_config.optionxform = lambda option: option  # type: ignore
    config_config.read(config_path)
    return config_config


def write_config_file(config: configparser.ConfigParser):
    """
    Write out a copy of ~/.aws/config.
    """
    confirm_aws_directory()
    config_path = Path("~/.aws/config").expanduser()
    with open(config_path, "w") as config_file:
        config.write(config_file)

def get_aliases(environment: str) -> dict:
    """
    Retrieve SSO account aliases for an environment.
    """
    config_section = f"sso_{environment}.aliases"
    aws_config = read_config_file()
    if config_section in aws_config.sections():
        return dict(aws_config[config_section])
    return {}

def get_sso_token(environment: str) -> dict:
    """
    Retrieve SSO token for an environment.
    """
    config_section = f"sso_{environment}"
    credentials_config = read_credentials_file()
    if config_section in credentials_config.sections():
        token = dict(credentials_config[config_section])
        if (token.keys() >= {"startUrl", "region", "accessToken", "expiresAt"}) and datetime.now(
            tzutc()
        ) < datetime.fromisoformat(token["expiresAt"]):
            # token in credentials file is valid for use (not expired), return it
            return token
    # no valid token available, get a new one
    token = request_new_sso_token(environment, credentials_config[config_section]["region"], credentials_config[config_section]["startUrl"])
    credentials_config[config_section] = token
    write_credentials_file(credentials_config)
    return token


def get_account_credentials(token: dict, environment: str, *, aliases:dict=None):
    """
    Retrieve credentials for all accessible accounts in AWS SSO and store them
    in ~/.aws/credentials.
    """
    config_section = f"sso_{environment}"
    credentials_config = read_credentials_file()
    sso_client = boto3.client("sso", region_name=credentials_config[config_section]["region"])
    accounts_paginator = sso_client.get_paginator("list_accounts")
    accounts_iterator = accounts_paginator.paginate(accessToken=token["accessToken"])
    accounts = {}
    # Get all accounts user has access to
    for accounts_page in accounts_iterator:
        accounts.update({account["accountId"]: account for account in accounts_page["accountList"]})
    roles_paginator = sso_client.get_paginator("list_account_roles")
    # Get all roles in all accounts user has access to
    for account in accounts.values():
        account["roles"] = {}
        roles_iterator = roles_paginator.paginate(accessToken=token["accessToken"], accountId=account["accountId"])
        for roles_page in roles_iterator:
            account["roles"].update({role["roleName"]: role for role in roles_page["roleList"]})
    # Get credentials for all account, role tuples
    credentials_config = read_credentials_file()
    for account in accounts.values():
        for role in account["roles"].values():
            try:
                role["roleCredentials"] = sso_client.get_role_credentials(
                    roleName=role["roleName"], accountId=role["accountId"], accessToken=token["accessToken"]
                )["roleCredentials"]
            except (sso_client.exceptions.InvalidRequestException,botocore.exceptions.ClientError):
                print(
                    f"Unable to retrieve credentials for account/role {role['accountId']}/{role['roleName']}",
                    flush=True,
                )
                continue
            credentials_config[f"{role['accountId']}_{role['roleName']}"] = {
                "aws_access_key_id": role["roleCredentials"]["accessKeyId"],
                "aws_secret_access_key": role["roleCredentials"]["secretAccessKey"],
                "aws_session_token": role["roleCredentials"]["sessionToken"],
                "sso_updated_on": str(datetime.now(tzutc())),
            }
            credentials_config[role["accountId"]] = credentials_config[f"{role['accountId']}_{role['roleName']}"]
            for alias, account_id in aliases.items():
                if account_id == f"{role['accountId']}_{role['roleName']}":
                    credentials_config[alias] = credentials_config[f"{role['accountId']}_{role['roleName']}"]
    write_credentials_file(credentials_config)


def getcreds(environments: list):
    """Get credentials from SSO and populate a credentials file."""

    tokens = {}
    for environment in environments:
        aliases = get_aliases(environment)
        tokens[environment] = get_sso_token(environment)
    for environment in environments:
        get_account_credentials(tokens[environment], environment, aliases=aliases)
    print("Credential update complete")
