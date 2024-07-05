# RODEO Work Package 5 - EDR Workshop

This workshop was given as part of the EUMETNET project RODEO, in the context of Work Package 5 (Climate data). The
workshop was given on 2024-06-13 and 2024-06-14 in Helsinki, Finland. See the [slides](WP5-EDR-workshop.pdf) of the
workshop if you would like to follow along.

## Getting started

Clone this repository
```shell
git clone https://github.com/EURODEO/wp5-edr-workshop.git
cd wp5-edr-workshop
```

Go to branch `step_0`  if you would like to follow the workshop steps. The `main` branch contains the full example.
```shell
git checkout step_0
```

It is recommended to use a Python virtual environment.
```shell
python3 -m venv venv/
```

You can install dependencies using `pip3` or `pip-sync` (from the `pip-tools` package)
```shell
pip3 install -r requirements.txt
```
or
```shell
pip3 install pip-tools
pip-sync
```

Run the API in debug mode using
```shell
uvicorn main:app --reload
```
This automatically reloads the API if you make any changes to the source.
It is also possible to start uvicorn directly using:

```shell
python3 main.py
```

## Step debugging

In Pycharm or Visual Studio Code, add `main.py` Python3 run configuration. This
will start uvicorn while still allowing to do step debugging inside the IDE.

## Visualization

A good place to visualize GeoSJON is [here](https://geojson.io/#map=2/0/20).
For CoverageJSON you can use the [Playground](https://covjson.org/playground/).

## Updating dependencies

To update the dependencies you can change `requirements.in` and run `pip-compile` from the `pip-tools` package.

```shell
pip3 install pip-tools
pip-compile --upgrade --no-emit-index-url
```
