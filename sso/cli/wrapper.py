"""sso.cli.wrapper - module defining `sso wrapper` subcommand."""
import click


@click.group()
def wrapper():
    """
    sso wrapper subcommand.
    """


@wrapper.command(short_help="Wrapper tool for sso")
@click.option("--output-file", default="/usr/local/bin/sso", required=False)
def install(output_file: str):
    """
    sso wrapper install subcommand.
    """
    print_sso_wrapper_installer(output_file=output_file)


def print_sso_wrapper():
    """
    Emit a sso shell wrapper to stdout.
    """
    print(
        """#!/bin/sh
if [ "${SSO_TAG}" = "" ]; then
  SSO_TAG="latest"  # by default, use latest push of moe:devtools for invoke
fi
if [ "${SSO_COMMAND}" = "" ]; then
  SSO_COMMAND="sso"  # by default, run the "sso" command
fi
SSO_DOCKER_ENV_OPTS="-e AWS_PROFILE -e AWS_DEFAULT_PROFILE -e AWS_ACCESS_KEY_ID"
SSO_DOCKER_ENV_OPTS="$SSO_DOCKER_ENV_OPTS  -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN -e HTTPS_PROXY"
SSO_DOCKER_VOL_OPTS="-v /var/run/docker.sock:/var/run/docker.sock"
SSO_DOCKER_VOL_OPTS="$SSO_DOCKER_VOL_OPTS -v $HOME/.aws:/root/.aws"
SSO_DOCKER_OPTS="${SSO_DOCKER_ENV_OPTS} ${SSO_DOCKER_VOL_OPTS}"
docker run --rm ${SSO_DOCKER_OPTS} ${SSO_DOCKER_EXTRA_OPTS} \
    sso:${SSO_TAG} ${SSO_COMMAND} $*
"""
    )


def print_sso_wrapper_installer(output_file: str):
    """
    Emit a shell script for installing sso wrapper.
    """
    print(f"cat > {output_file} <<'EOF'")
    print_sso_wrapper()
    print("EOF")
    print(f"chmod 755 {output_file}")
