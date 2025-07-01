#!/bin/bash

# Change to the correct directory
# Store the script's directory path
SCRIPT_DIR="$(dirname "$0")"

# Change to the script's directory, exit if failed
cd "${SCRIPT_DIR}" || exit 1


#!/bin/bash

#!/bin/bash

# ====================
# Virtual Environment Activation Script
# Purpose: Activates Python virtual environment with validation
# ====================

# Configuration
readonly VENV_DIR=".venv"
readonly VENV_ACTIVATE="${VENV_DIR}/bin/activate"
readonly ERROR_PREFIX="ERROR:"
readonly SUCCESS_PREFIX="SUCCESS:"

check_venv_exists() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "${ERROR_PREFIX} Virtual environment not found at '${VENV_DIR}'"
        echo "Please create virtual environment using: python -m venv ${VENV_DIR}"
        return 1
    fi
    return 0
}

activate_venv() {
    echo "Activating virtual environment..."
    if source "$VENV_ACTIVATE"; then
        echo "${SUCCESS_PREFIX} Virtual environment activated successfully"
        return 0
    else
        echo "${ERROR_PREFIX} Failed to activate virtual environment at '${VENV_ACTIVATE}'"
        return 1
    fi
}

# Main execution
if check_venv_exists; then
    activate_venv || exit 1
else
    exit 1
fi
# Run the main application using the installed package
# python -m skinnerbox.skinnerbox.main

# Alternative method if the module approach doesn't work
python -c "import skinnerbox; skinnerbox.main()"