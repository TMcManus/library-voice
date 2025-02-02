# LibraryVoice  
### Objective
Enable terminal users/AI agents to capture verbose command outputs into files and automatically replace them with succinct summaries.

### Problem  
AI coding assistants like Cline use terminal outputs to debug and iterate. Unfortunately, verbose terminal outputs (stack traces, install logs) **waste token context space**, increasing costs and reducing focus.

### Solution
The best solution to this problem is for [AI coding assistant to consider the level of verbosity](https://github.com/cline/cline/issues/1537) that will result from the comand they are about to run. But if you can't depend on that, you can use this tool to shush your shell.

This tool activates a terminal mode that:
1. Suppresses raw outputs by default.
2. **Immediately returns either** a short output (if under 200 characters) or a concise summary.  
3. **Stores raw logs** locally with IDs for manual review if needed.

## Usage

### Activating
To start redirecting and processing command output:
```zsh
source lv.zsh
```
This will:
1. Set up shell hooks to track command execution
2. Create necessary control signals infrastructure
3. Start the output processor
4. Begin redirecting all STDOUT and STDERR through the processor

### Deactivating
There are two ways to deactivate the output processing:

1. Close the current terminal and open a new one (recommended, but requires manual cleanup of the Python process the script creates, see critical issue later in the doc)
2. (not really working yet) Or run these commands to restore normal output:
```zsh
# Kill the background process
kill $PID_PROCESS_OUTPUT
# Reset output redirection
exec >/dev/tty 2>&1
```

## Processing
All command output is processed by `library_voice.py` and:
1. Written in full to process-specific log files (`lv-{timestamp}-{process_id}.log`)
2. Displayed in the terminal either in full (if under 200 characters) or truncated with "..."

## Expected Output
### Terminal
Once the script is active running commands should look like this in the terminal:
```zsh
$ ls
[2025-01-30 15:27:57]
README.md
file_1.txt
file_2.txt
```
Commands with longer output should look like this in the terminal:
```zsh
$ ollama list
[2025-01-30 15:27:59]
NAME                          ID              SIZE      MODIFIED    
llama2:latest                 78e26419b446    3.8 GB    3 days ago     
llama3.2:1b                   baf6a787fdff    1.3 GB    3 d...
```
### Log Files
The system creates log files that look like `lv-{timestamp}-{process_id}.log` (in the same directory currently) when lv.zsh is sourced. These logs contain complete, untruncated output for all the commands.

The script filters certain terminal control sequences (like OSC7 and ANSI escape sequences) to prevent display issues and infinite output loops that can casue crashes.

Example terminal output log content:
```
[2025-01-30 15:27:57]
README.md
file_1.txt
file_2.txt
[2025-01-30 15:27:59]
NAME                          ID              SIZE      MODIFIED    
llama2:latest                 78e26419b446    3.8 GB    3 days ago     
llama3.2:1b                   baf6a787fdff    1.3 GB    3 days ago     
deepseek-r1:14b               ea35dfe18182    9.0 GB    8 days ago     
mxbai-embed-large:latest      468836162de7    669 MB    9 days ago     
phi4:latest                   ac896e5b8b34    9.1 GB    13 days ago    
qwen2.5:0.5b-instruct-q5_0    4a8f6fc82b6e    396 MB    3 weeks ago    
llama3.2-vision:latest        085a1fdae525    7.9 GB    3 weeks ago    
llama3.1:latest               46e0c10c039e    4.9 GB    3 weeks ago
```

## Known Issues

### Critical
- The python script runs 100% CPU on one thread everytime you use it
- Process cleanup is not reliable - manual process killing is currently required after using the script
- It's important to manually kill these processes once you're done using the script

### Major
- Current escape sequence filtering may not catch all cases
- Additional testing with various shells is needed to identify missing escape sequences

## Future Improvements
1. **Performance & Reliability**
   - Port Python portions to Go or Rust for better performance. I asked Claude to port the python to Go and it worked great, but I can't read Go so I don't really feel comfortable using that.

2. **Configuration & Testing**
   - Add user configuration for truncation limits
   - Allow customization of log file locations
   - Implement testing

3. **Shell Compatibility**
   - Test with wider variety of shells
   - Improve escape sequence filtering
