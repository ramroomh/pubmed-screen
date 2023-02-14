# PubMed Screen

Automates the initial screening phase of systematic PubMed search using keywords.

## Developing

To install this package for development on Linux:

1) Create a virtual environment.

```
$ python3 -m venv venv
$ source venv/bin/activate
```

2) Install an editable development version of the package with `pip`.

```
$ pip3 install --editable .[dev]
```

3) Edit the `src/pubmed_screen/main.py` file to make changes.

4) Run the script with the `pmscreen` command that was installed by pip.

```
$ pmscreen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Welcome to PubMed Screen.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PubMed Screen allows you to optimize your search strategy.
Would you like to create a search (enter: 1) or compare searches (enter: 2)?
```
