# RODEO Work Package 5 - EDR Workshop

## Getting started

It is recommended to use a Python virtual environment.

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
