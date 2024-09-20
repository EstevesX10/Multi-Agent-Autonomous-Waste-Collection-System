<div align="center">

# Project Setup [Ubuntu]
</div>

This project focuses on managing an ``Autonomous Intelligent Multi-Agent Environment``, which involves integrating various technologies: ``pyenv`` for **Python version management**, an ``XMPP server`` for **agent communication**, and the ``SPADE`` framework to **enable multi-agent interactions**. These components work together to bring the system to life, facilitating seamless **communication and coordination** among **intelligent agents**.

## Python and Virtual Environment Installation

In order to install important packages for the projects development with:

    sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \ libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \ xz-utils tk-dev libffi-dev liblzma-dev openssl git

Fetch and execute the installation script of pyenv

    curl https://pyenv.run | bash

To ensure that pyenv knows where to store and manage Python versions and related tools, you must execute:

    export PYENV_ROOT=”$HOME/.pyenv”

It is important to check if pyenv is already available in the system's command path. If it is not found, we need to add pyenv to the PATH environment variable. Therefore, just run:

    command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"

To ensures that pyenv is fully integrated into the shell, perform:

    eval "$(pyenv init -)"

To initialize the pyenv-virtualenv plugin, execute:

    eval "$(pyenv virtualenv-init -)”

To install the correct Python version using ``pyenv``, ensure you restart the shell and run the following command:

    pyenv install 3.9.5

This command will ensure that Python 3.9.5 is properly installed within pyenv.

To create a new virtual environment use:

    pyenv virtualenv <PYTHON_VERSION> <ENV_NAME>

To activate a Virtual Environment, simply run:

    pyenv activate <ENV_NAME>

To visualize all the available virtual environments execute:

    pyenv versions

## XMPP Server (Prosody)

An XMPP server running locally is required to use SPADE, otherwise, the agents won't be able to communicate through messages. Since SPADE recommends using Prosody, that's the server we will use.

### Prosody Installation

To install prosody, you can enter this command on your bash terminal:

    sudo apt install prosody

### Configuration File [prosody.cfg.lua]

To correctly set up the Prosody server, it's essential to modify its configuration file.

First, locate the **prosody.cfg.lua** file inside the ``/etc/prosody/prosody.cfg.lua`` directory. Once inside the file, make sure to adjust the following parameters:

- Virtualhost "localhost"
- admins = { "admin@localhost" }
- s2s_secure_auth = false
- Allow_registration = true
- pidfile = "prosody.pid"

### Create an Account

If you are looking to create an account on the server, there are two viable options. On one side you can use:

    sudo prosodyctl adduser <UserName>@<VirtualHostName>

and enter a password for the new user. On the other, it is possible to proccess this registration with a single command:

    sudo prosodyctl register <UserName> <VirtualHostName> <UserPassword>

For instance, you can execute:

    - sudo prosodyctl adduser admin@localhost [And add a password]
    - sudo prosodyctl register admin localhost password

### Useful prosody commands

There are a few useful prosody commands that can help you better manage the activities of the XMPP server:

- Show the status of the server
    
        sudo prosodyctl status

- Start the Server
    
        sudo prosodyctl start

- Stop the Server
    
        sudo prosodyctl stop

- Perform a check on the Server
    
        sudo prosodyctl stop

## SPADE Installation

Before proceeding with the installation of SPADE, ensure that you have set up a Virtual Environment following the instructions given above.

First, in the project's directory, activate the previously created pyenv environment by running:

    pyenv activate <ENV_NAME>

Once the environment is activated, install SPADE with the following command:

    pip install spade