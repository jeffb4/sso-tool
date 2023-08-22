# sso

Command-line utility and helper.

## Getting Started

### Building

    make docker-build

### Installing sso wrapper

This creates a shell script at `/usr/local/bin/sso` for running the script.

    docker run sso sso wrapper install | sh

### Installing sso wrapper as root

    docker run sso sso wrapper install | sudo sh

### Configuration

Currently, the SSO client supports two runtime environments "dev" and "prod". By
default, the client will retrieve "dev" credentials and not "prod". If you don't
have multiple AWS SSO URLs, you can configure everything for the "dev" environment
and be happy. In the future, the utility will be modified to read environments
from configuration and not code.

`~/.aws/config`

```
[default]
region = us-west-2

[sso_dev]
startUrl = https://myssourl.awsapps.com/start#/
region = us-west-2

[sso_dev.aliases]
int = 12345_AWSAdministratorAccess
prod = 56789_AWSAdministratorAccess
dev = 34567_AWSAdministratorAccess
```

### Running

    sso getcreds

The script will emit a URL for the user to go to in their browser. AWS SSO will handle any
authentication needed, and the `sso` utility will then use oauth to access the AWS SSO API.

The `sso` utility will create a profile in `~/.aws/credentials` with every account, role pair
available to the user. In addition, short aliases can be defined (see above). It is recommended
that a `~/.aws/config` profile entry be created with default regions for accounts, but is not
required.

## Authors

- **Jeff Bachtel** - _Initial work_ - [github](https://github.com/jeffb4)

See also the list of [contributors](https://github.com/jeffb4/sso/contributors) who participated in this project.

## LicenseCopyright (c) Jeff Bachtel

All rights reserved.
