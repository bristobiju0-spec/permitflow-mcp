#!/bin/bash
# Wrapper script to run the permitflow mcp server using the local venv

# Get the script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Run the server using the venv python
"$DIR/venv/bin/python" "$DIR/mcp_server.py" "$@"
