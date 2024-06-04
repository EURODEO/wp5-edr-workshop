# wp5-edr-workshop

## Getting started

It is recommended to use a Python virtual environment.

You can install dependencies using `pip3` or `pip-sync` (from the `pip-tools` package)
```shell
pip3 install -r requirements.txt
```

## Updating dependencies

To update the dependencies you can change `requirements.in` and run `pip-compile` from the `pip-tools` package.

```shell
pip3 install pip-tools
pip-compile --upgrade --no-emit-index-url
```
