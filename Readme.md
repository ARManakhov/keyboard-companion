# Keyboard Companion

Companion app for QMK keyboard, that communicates via rawHID

## Capabiltites

## Installation

```bash
flatpak-builder --install --user --force-clean build-dir manifest.yaml
```

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/sync.py
```


