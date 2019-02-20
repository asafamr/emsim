#!/usr/bin/env bash

read -p "This script will install all python packages and spacy models in the current env. Are you sure? " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
     exit 1 || return 1 # handle exits from shell or function but don't exit interactive shell
fi

if [ ! -f .env ]; then
echo creating .env file - make sure dataset path in .env file is ok
    cp .env.example .env
fi

echo installing python requirements from requirements.txt...
pip install -r requirements.txt

echo downloading spacy glove vectors...
python -m spacy download en_core_web_lg