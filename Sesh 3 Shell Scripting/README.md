# System Information Script

A simple Bash script that gathers and displays key system information, then saves the currently running processes to a log file of the user's choosing.

---

## What the Script Does

* Prints the current date and time.
* Prints the system hostname.
* Prints the currently logged-in username.
* Prints disk usage (`df -h`).
* Prints running processes (`ps aux`) — a quick preview in the terminal.
* Uses variables to store command outputs and user input.
* Takes user input using `read -p` for a directory name and a log filename (with sensible defaults if left blank).
* Creates a directory using `mkdir`.
* Creates a file using `touch`.
* Stores the full running processes list in the file using `>` output redirection.

---

## Commands Used

| Command | Purpose in the Script |
| :--- | :--- |
| `date` | Fetches the current date and time. |
| `hostname` | Fetches the system hostname. |
| `whoami` | Fetches the active username. |
| `df -h` | Displays human-readable disk usage. |
| `ps aux` | Lists all running processes. |
| `read -p` | Prompts the user for directory/file names. |
| Variables | Store command outputs and user input for reuse. |
| `mkdir` | Creates the target log directory. |
| `touch` | Creates the empty log file before writing to it. |
| `>` | Redirects `ps aux` output into the log file. |

---

## Prerequisites

* A Linux/Unix environment with `bash` installed.
* Standard coreutils (`df`, `ps`, `hostname`, `whoami`) available on the system.

---

## How to Run

1. Give the script execute permission:

   ```bash
   chmod +x system_info.sh
   ```

2. Run the script:

   ```bash
   ./system_info.sh
   ```

3. When prompted, enter a directory name and a log file name, or press **Enter** to accept the defaults:

   ```text
   Enter directory name to create [default: system_logs]:
   Enter log filename to save running processes [default: process_list.txt]:
   ```

---

## Sample Output

```text
====================================================
               SYSTEM INFORMATION REPORT
====================================================

[+] Current Date & Time : Thu Sep  3 10:15:42 IST 2026
[+] System Hostname     : ubuntu-server
[+] Active Username     : devops_user

====================================================
                 DISK USAGE OVERVIEW
====================================================

Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        40G   12G   26G  32% /

====================================================
              RUNNING PROCESSES (PREVIEW)
====================================================

USER   PID %CPU %MEM COMMAND
root     1  0.0  0.1 /sbin/init
...

====================================================
           SAVE PROCESS LIST TO FILE
====================================================

[+] Setting up log directory and process file...
Enter directory name to create [default: system_logs]:
Enter log filename to save running processes [default: process_list.txt]:

[+] Processing your input...
[+] Executing: mkdir -p system_logs
[+] Executing: touch system_logs/process_list.txt
[+] Collecting running processes using 'ps aux'...

====================================================
                     SUCCESS!
====================================================
 Log Saved At  : system_logs/process_list.txt
 Log File Size : 4523 bytes
 Total Lines   : 62 lines

[+] First 10 lines of stored processes log:
USER   PID %CPU %MEM COMMAND
root     1  0.0  0.1 /sbin/init
...

====================================================
               SCRIPT COMPLETED
====================================================
```

---

## Output

After running the script, a directory (default: `system_logs/`) is created containing a text file (default: `process_list.txt`) with the full output of `ps aux` at the time the script was run.

---

## Notes

* If the specified directory already exists, `mkdir -p` will not throw an error — it simply reuses it.
* If left blank, the directory and filename prompts fall back to `system_logs` and `process_list.txt` respectively, using Bash parameter expansion: `${VAR:-default}`.
* The script overwrites the target file each time it runs (single `>` redirection), so re-running it will refresh the log with the latest process snapshot.
