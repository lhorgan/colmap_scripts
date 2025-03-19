import subprocess
import time
import sys

def is_process_running(process_name):
    """Check if a process with the given name is running."""
    try:
        # Using ps and grep to find the process, excluding the grep process itself
        result = subprocess.run(
            f"ps u | grep '{process_name}' | grep -v grep", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        # If output is not empty, process is running
        return result.stdout.find(process_name) >= 0
    except Exception as e:
        print(f"Error checking process: {e}")
        return False

def monitor_until_process_ends(process_name, check_interval=10):
    """
    Monitor a process and exit when it's no longer running.
    
    Args:
        process_name: Name of the process to check
        check_interval: Time in seconds between checks
    """
    print(f"Monitoring process '{process_name}'...")
    
    while True:
        if not is_process_running(process_name):
            print(f"Process '{process_name}' has ended. Exiting monitor.")
            sys.exit(0)
        
        time.sleep(check_interval)

if __name__ == "__main__":        
    process_to_monitor = "glomap"
    monitor_until_process_ends(process_to_monitor)