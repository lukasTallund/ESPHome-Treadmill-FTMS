#!/usr/bin/env bash
# Project-local shell aliases. Not loaded automatically - source this file
# from a shell in the repo root when you want them:
#
#   source tools/aliases.sh
#
# Or add that line to your ~/.bashrc / ~/.zshrc to have them everywhere.
#
# --no-states drops the CLI's per-entity "[S] 'Name' >> value" state feed
# (see tools/translate_log.py for the Russian->English log translation).

alias tm-logs='esphome logs esphome/config.yaml --no-states | python3 tools/translate_log.py'
alias tm-run='esphome run esphome/config.yaml --no-states | python3 tools/translate_log.py'
