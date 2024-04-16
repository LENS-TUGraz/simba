# *Simba*: Batteryfree-node-simulator

This repo contains the *Simba* simulation framework, including its source code, tools, example simulations, and documentation files.

### Folder structure

| **Folder** | **Description** |
|---|---|
| Artifacts | Measured data from evaluation experiments |
| Simba | Simba simulation core and module implementations |
| Simulations | Example simulations and simulations from paper |
| Tools | Tools and utilities |
| docs | Simba's documentation source files |

## Documentation
More details about the implementation and the available modules can be found in *Simba*'s documentation at: https://lens-tugraz.github.io/simba/

## Using *Simba*

To use the simulation framework, use one of the following installation methods:

### 1) Run within VSCode Devcontainer

We recommend to run *Simba* using VSCode and its Devcontainer extension.
To this end, simply install [Docker](https://www.docker.com/products/docker-desktop/) and [VSCode](https://code.visualstudio.com/) and all the remaining software and packages will be installed automatically within a [Devcontainer](https://code.visualstudio.com/docs/devcontainers/containers). This way, no cumbersome manual installation is required and a seamless deinstallation is also possible.

#### Setup Option 1: Store *Simba* locally and run within VSCode Devcontainer

- Clone this repo (`git clone ....`) to the desired location.
- Install the [Devcontainer Extension](...) in VSCode.
- Open VSCode, press `F1`, run `Dev Container: Open Folder in Container`, and select the location of this repo.
- VSCode will continue to setup your container and install the required VSCode extensions.

#### Setup Option 2: Store *Simba* in container and run within VSCode Devcontainer
[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/simbaframework/simba.git)

You can also directly click the badge above or [here](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/simbaframework/simba.git) to get started. Clicking these links will cause VS Code to automatically install the Dev Containers extension if needed, clone the source code into a container volume, and setup up the container for your use.

#### Using *Simba* in VSCode

Once the Devcointainer is installed, VSCode offers an convenient way to use *Simba* using its *Jupyter* extension and *Interactive Python mode*. This extension is installed automatically in the Devcontainer.
To run a simulation, open the corresponding simulation file in VSCode (e.g., *Simulations/sim_examples_iin_capsize.py*), press `Strg + Shift + P` and select `Jupyter: Run All Cells`.
VSCode will then execute your python code, display plots, show variables content etc. 
For more information how to use *Python Interactive mode* in VSCode, see https://code.visualstudio.com/docs/python/jupyter-support-py.

### 2) Run fully locally

To run *Simba* locally (recommend for development and long-term simulations), clone this repo and install the required Python packages as well as the simulation core using:
```
cd <SIMBA_REPO_FOLDER>
pip3 install --user -r requirements.txt
pip3 install --user --editable Simba
```
You can now use Simba like any other Python package and we recommend the usage within an IDE (e.g., [Spyder](https://www.spyder-ide.org/) has proven to be very convenient).
