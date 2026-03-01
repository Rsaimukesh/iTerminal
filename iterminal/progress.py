"""Progress tracking and visualization for command execution."""
import subprocess
import threading
import time
from typing import Tuple, Optional, Callable
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn
from rich.live import Live
from rich.text import Text
import re

console = Console()


class ProgressTracker:
    """Track and visualize command execution progress."""
    
    def __init__(self, cmd: str, show_progress: bool = True):
        """
        Initialize progress tracker.
        
        Args:
            cmd: Command being executed
            show_progress: Whether to show progress bar
        """
        self.cmd = cmd
        self.show_progress = show_progress
        self.returncode = -1
        self.stdout = ""
        self.stderr = ""
        self.progress = None
        self.task_id = None
        self.start_time = None
        self.is_apt_command = self._is_apt_command()
        self.total_packages = 0
        self.processed_packages = 0
        
    def _is_apt_command(self) -> bool:
        """Check if this is an apt/apt-get command that benefits from progress tracking."""
        return any(cmd in self.cmd.lower() for cmd in ['apt update', 'apt upgrade', 'apt install', 'apt-get'])
    
    def _extract_apt_progress(self, line: str) -> Optional[Tuple[int, int]]:
        """Extract progress from apt command output."""
        # Pattern: "Get:123 http://..." or similar
        get_match = re.search(r'Get:(\d+)', line)
        if get_match:
            current = int(get_match.group(1))
            # Try to find total packages
            total_match = re.search(r'Get:(\d+).*of (\d+)', line)
            if total_match:
                return int(total_match.group(1)), int(total_match.group(2))
            return current, None
        
        # Pattern: "Setting up package-name..."
        if 'Setting up' in line or 'Unpacking' in line:
            return 1, 1
        
        return None
    
    def execute_with_progress(self) -> Tuple[int, str, str]:
        """
        Execute command with progress tracking.
        
        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        if not self.show_progress:
            return self._execute_simple()
        
        self.start_time = time.time()
        
        # For apt commands, show detailed progress
        if self.is_apt_command:
            return self._execute_with_apt_progress()
        else:
            return self._execute_with_spinner()
    
    def _execute_simple(self) -> Tuple[int, str, str]:
        """Execute command without progress tracking."""
        try:
            process = subprocess.Popen(
                self.cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
        except Exception as e:
            return -1, "", str(e)
    
    def _execute_with_spinner(self) -> Tuple[int, str, str]:
        """Execute command with spinner progress indicator."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Executing:[/cyan] {self.cmd[:60]}{'...' if len(self.cmd) > 60 else ''}",
                    total=None
                )
                
                process = subprocess.Popen(
                    self.cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                # Read output line by line
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    self.stdout += line
                
                # Get stderr
                stderr_data = process.stderr.read()
                self.stderr += stderr_data
                
                # Wait for process to complete
                self.returncode = process.wait()
        
        except Exception as e:
            self.returncode = -1
            self.stderr = str(e)
        
        return self.returncode, self.stdout, self.stderr
    
    def _execute_with_apt_progress(self) -> Tuple[int, str, str]:
        """Execute apt command with detailed progress tracking."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
                transient=False,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Installing packages...[/cyan]",
                    total=100,
                    start=True
                )
                
                process = subprocess.Popen(
                    self.cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Track lines for progress estimation
                line_count = 0
                packages_processed = 0
                
                for line in process.stdout:
                    self.stdout += line
                    line_count += 1
                    
                    # Update progress based on keywords
                    if 'Get:' in line:
                        packages_processed += 1
                        progress.update(task, advance=0.5)
                    elif 'Setting up' in line or 'Unpacking' in line:
                        progress.update(task, advance=5)
                    elif 'Processing triggers' in line:
                        progress.update(task, advance=30)
                    elif 'Reading' in line or 'Building' in line:
                        progress.update(task, advance=1)
                    
                    # Update description with current action
                    if 'Setting up' in line:
                        package_name = line.split('Setting up')[-1].strip().split('(')[0].strip()
                        progress.update(task, description=f"[cyan]Installing:[/cyan] {package_name[:50]}")
                    elif 'Reading package' in line:
                        progress.update(task, description="[cyan]Reading package lists...[/cyan]")
                    elif 'Building' in line:
                        progress.update(task, description="[cyan]Building dependency tree...[/cyan]")
                
                # Complete the progress bar
                progress.update(task, completed=100)
                
                # Get stderr if it exists
                self.returncode = process.wait()
        
        except Exception as e:
            self.returncode = -1
            self.stderr = str(e)
        
        return self.returncode, self.stdout, self.stderr


def execute_with_progress(cmd: str, show_progress: bool = True) -> Tuple[int, str, str]:
    """
    Execute a shell command with progress tracking.
    
    Args:
        cmd: Command to execute
        show_progress: Whether to show progress bar
    
    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    # Determine if we should show progress based on command type
    should_show_progress = show_progress and any(
        pkg_cmd in cmd.lower() for pkg_cmd in ['apt', 'yum', 'dnf', 'pacman', 'pip']
    )
    
    tracker = ProgressTracker(cmd, show_progress=should_show_progress)
    return tracker.execute_with_progress()
