#!/usr/bin/env bash
PORT="$(python -c 'import os;import dotenv;dotenv.load_dotenv();print(os.environ["PORT"])')"
HOST="$(python -c 'import os;import dotenv;dotenv.load_dotenv();print(os.environ["HOST"])')"

gunicorn --timeout 600 -b $HOST:$PORT  server:app