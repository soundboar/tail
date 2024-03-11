# soundboar/tail - the soundboards CLI and python backend

Soundboar offers a web-accessible soundboard for self-hosting (e.g. on a Raspberry-Pi connected to a speaker).
To install the soundboard on your machine, just install it from via pip:

```shell
$ pipx install soundboar
$ soundboar run # Installs the data-repo and webserver in its default location
```

For more information run

```shell
$ soundboar --help
```

For developing soundboar, clone the repository, create a virtual environment, and run in its root

```shell
$ poetry install
```
