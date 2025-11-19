# Hiveden

A CLI tool and REST API for managing your personal server.

## Installation

```bash
pip install .
```

## Usage

### CLI

```bash
hiveden --help
```

### API

To run the API server, use the following command:

```bash
uvicorn hiveden.api.server:app --reload
```
