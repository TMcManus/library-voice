#!/usr/bin/env python3
import sys
import os
import datetime
import select
import fcntl

class OutputProcessor:
    def __init__(self):
        self.buffer = bytearray()
        self.in_command = False
        self.current_command = None
        self.output_file = os.getenv('LV_LOG_FILE')
        self.fifo_path = '/tmp/cmd_control'
    
    def is_osc7_sequence(self, data):
        """Check if buffer contains an OSC 7 terminal sequence"""
        return b']7;file://' in data
        
    def is_ansi_escape_sequence(self, data):
        """Check if buffer contains ANSI escape sequences"""
        # Common ANSI escape sequences start with ESC[ (27, 91 in ASCII)
        return bytes([27, 91]) in data
        
    def truncate_text(self, text, max_length=200):
        """Truncate text to max_length characters, adding ... if truncated"""
        text = text.rstrip('\n')
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
        
    def process_control_signal(self, signal_text):
        """Process control signals from the FIFO"""
        signal_text = signal_text.strip()
        
        if signal_text.startswith("__CMD_START__:"):
            self.in_command = True
            self.current_command = signal_text.split(":", 1)[1]
            self.buffer.clear()
        elif signal_text == "__CMD_END__":
            if self.buffer:
                self.process_buffer()
            self.in_command = False
            
    def process_buffer(self):
        """Process and write the current buffer contents"""
        if not self.buffer:
            return
            
        # DO NOT REMOVE. RISK OF INFINITE LOOP.
        # Filter out OSC 7 and ANSI escape sequences
        if self.is_osc7_sequence(self.buffer) or self.is_ansi_escape_sequence(self.buffer):
            self.buffer.clear()
            return
            
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = self.buffer.decode('utf-8', errors='replace').rstrip()
        
        # Write full content to log file
        with open(self.output_file, 'a') as f:
            f.write(f"[{timestamp}]\n{text}\n")
            f.flush()
        
        # Write truncated content to terminal with extra newline
        sys.stderr.write(f"[{timestamp}]\n{self.truncate_text(text)}\n\n")
        sys.stderr.flush()
        
        # Clear buffer
        self.buffer.clear()

def main():
    processor = OutputProcessor()
    
    # Set up non-blocking reads for STDIN
    stdin_fd = sys.stdin.fileno()
    flags = fcntl.fcntl(stdin_fd, fcntl.F_GETFL)
    fcntl.fcntl(stdin_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    
    # Open FIFO for reading control signals
    fifo = open(processor.fifo_path, 'r')
    fifo_fd = fifo.fileno()
    
    try:
        while True:
            # Wait for input with timeout
            try:
                ready, _, _ = select.select([stdin_fd, fifo_fd], [], [], 0.1)
            except select.error:
                break
            
            if not ready:
                continue
            
            for fd in ready:
                if fd == stdin_fd:
                    # Read from STDIN
                    try:
                        chunk = os.read(stdin_fd, 1024)
                        if not chunk:  # EOF
                            if processor.buffer:
                                processor.process_buffer()
                            break
                        processor.buffer.extend(chunk)
                    except (BlockingIOError, OSError):
                        continue
                        
                elif fd == fifo_fd:
                    # Read control signal
                    try:
                        signal_text = fifo.readline()
                        if not signal_text:  # EOF
                            if processor.buffer:
                                processor.process_buffer()
                            break
                        processor.process_control_signal(signal_text)
                    except (IOError, OSError):
                        break
                    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        sys.stderr.write(f"Error processing input: {str(e)}\n")
        sys.exit(1)
    finally:
        fifo.close()

if __name__ == "__main__":
    main()
