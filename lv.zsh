#!/usr/bin/env zsh

# Generate unique log file name
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
PROCESS_ID=$$
export LV_LOG_FILE="lv-${TIMESTAMP}-${PROCESS_ID}.log"

# Create FIFO for control signals if it doesn't exist
FIFO_PATH="/tmp/cmd_control"
[[ -p $FIFO_PATH ]] || mkfifo $FIFO_PATH

SCRIPT_DIR=${0:a:h}

# Hook that runs before command execution
preexec() {
    # Signal start of command output
    echo "__CMD_START__:$1" > $FIFO_PATH
}

# Hook that runs after command completion
precmd() {
    # Signal end of command output
    echo "__CMD_END__" > $FIFO_PATH
    # Force prompt redraw
    zle reset-prompt 2>/dev/null || true
}

# Set terminal title
echo -ne "\033]0;LibraryVoice\007"

# Store the process ID of our output processor
PID_PROCESS_OUTPUT=""

# Cleanup on exit
cleanup() {
    # Kill the output processor if it exists
    if [[ -n "$PID_PROCESS_OUTPUT" ]]; then
        kill $PID_PROCESS_OUTPUT 2>/dev/null || true
    fi
    # Remove the FIFO
    rm -f $FIFO_PATH
}
trap cleanup EXIT INT TERM HUP

# Set up output redirection through the processor
exec > >($SCRIPT_DIR/library_voice.py) 2>&1
PID_PROCESS_OUTPUT=$!
