<<<<<<< HEAD
# *Simba*: Batteryfree-node-simulator
=======
# Simba: Batteryfree-node-simulator
>>>>>>> 7041bb6 (Initial commit.)

This repo contains the *Simba* simulation framework, including its source code, tools, example simulations, and documentation files.

## General
This repo is still in progress, but already contains a complete and working version of the Simba simulation framework along with several example simulations.
The repo will be extended (e.g., with docu and more examples etc.) throughout the next weeks.

## Using *Simba*

To use the simulation framework, use one of the following installation methods:

### 1) Run within VSCode Devcontainer

We recommend to run *Simba* using VSCode and its Devcontainer extension.
To this end, simply install [Docker](https://www.docker.com/products/docker-desktop/) and [VSCode](https://code.visualstudio.com/) and all the remaining software and packages will be installed automatically within a [Devcontainer](https://code.visualstudio.com/docs/devcontainers/containers). This way, no cumbersome manual installation is required and a seamless deinstallation is also possible.

#### Setup: Store *Simba* locally and run within VSCode Devcontainer

- Clone this repo (`git clone ....`) to the desired location.
- Install the [Devcontainer Extension](...) in VSCode.
- Open VSCode, press `F1`, run `Dev Container: Open Folder in Container`, and select the location of this repo.
- VSCode will continue to setup your container and install the required VSCode extensions.

#### Using *Simba* in VSCode

Once the Devcointainer is installed, VSCode offers an convenient way to use *Simba* using its *Jupyter* extension and *Interactive Python mode*. This extension is installed automatically the Devcontainer.
To run a simulation, open the corresponding simulation file in VSCode (e.g., *Simulations/sim_examples_iin_capsize.py*), press `Strg + Shift + P` and select `Jupyter: Run All Cells`.
VSCode will then execute your python code, display plots, show variables content etc. 
For more information how to use *Python Interactive mode* in VSCode, see https://code.visualstudio.com/docs/python/jupyter-support-py.

### 3) Run fully locally

<<<<<<< HEAD
To run *Simba* locally (recommend for development and long-term simulations), clone this repo and install the required Python packages as well as the simulation core using:
```
cd <SIMBA_REPO_FOLDER>
pip3 install --user -r requirements.txt
pip3 install --user --editable Simba
```
You can now use Simba like any other Python package and we recommend the usage within an IDE (e.g., [Spyder](https://www.spyder-ide.org/) has been proven very convenient).
=======
TODO: Description.
>>>>>>> 7041bb6 (Initial commit.)
