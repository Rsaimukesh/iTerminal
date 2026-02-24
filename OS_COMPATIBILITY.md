# OS Compatibility Guide

## Current Status

### ✅ **Fully Supported**

- **Linux** (All distributions)
  - Ubuntu, Debian, Fedora, CentOS, Arch, Alpine, etc.
  - Tested on: Ubuntu 20.04+, Debian 11+, Fedora 35+

### ⚠️ **Not Currently Supported**

- **macOS** - *Can be adapted*
- **Windows** - *Can be adapted with WSL2*
- **Other Unix** - *Likely to work with modifications*

---

## Detailed OS Support

### 1. Linux ✅ (100% Compatible)

**Status:** Full support - iTerminal is designed for Linux.

```bash
# Install and run
pip install -r requirements.txt
python -m iterminal.cli

# Or system-wide
pip install -e .
iterminal
```

**Supported Distributions:**
- Ubuntu/Debian (apt)
- Fedora/CentOS/RHEL (dnf/yum)
- Arch Linux (pacman)
- Alpine (apk)
- OpenSUSE (zypper)
- Any distribution with bash/sh

**Hardware:**
- x86_64 ✅
- ARM64 ✅ (Raspberry Pi, etc.)
- ARM32 ⚠️ (may need smaller models)

---

### 2. macOS ⚠️ (Adaptable)

**Current Status:** Not officially supported, but **can be adapted**.

**Why it doesn't work out of the box:**
- Uses Linux-specific shell commands
- Assumes bash/bash 4.0+
- Package manager references (apt, dnf, etc.)
- /proc filesystem paths

**How to Make it Work:**

#### Option A: Using macOS Native (30 min work)

```bash
# 1. Create adapter for macOS commands
cat > iterminal/os_adapter.py << 'EOF'
import platform

def get_package_manager():
    """Get system package manager"""
    if platform.system() == "Darwin":  # macOS
        return "brew"
    elif platform.system() == "Linux":
        # Detect Linux package manager
        return detect_linux_pm()
    return None

def translate_command(cmd):
    """Translate Linux commands to macOS equivalents"""
    replacements = {
        "apt": "brew",
        "apt-get": "brew",
        "apt-cache": "brew",
        "dpkg": "brew",
        "dnf": "brew",
        "yum": "brew",
        "pacman": "brew",
        "systemctl": "launchctl",
    }
    for linux_cmd, mac_cmd in replacements.items():
        cmd = cmd.replace(linux_cmd, mac_cmd)
    return cmd

def is_command_compatible(cmd):
    """Check if command works on current OS"""
    # Add OS-specific compatibility checks
    pass
EOF

# 2. Update shell.py to use adapter
# Replace package manager references with adapter
# Replace Linux-specific paths with OS-agnostic ones
```

#### Option B: Using Docker (5 min, recommended)

```bash
# Run iTerminal in Docker container
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

CMD ["python", "-m", "iterminal.cli"]
EOF

# Build and run
docker build -t iterminal .
docker run -it iterminal
```

#### Option C: Using Homebrew

```bash
# Install dependencies via Homebrew
brew install bash@4 gnu-sed gnu-coreutils

# Ensure GNU versions are in PATH
export PATH="/usr/local/opt/gnu-sed/libexec/gnubin:$PATH"
export PATH="/usr/local/opt/gnu-coreutils/libexec/gnubin:$PATH"

# Run iTerminal
python -m iterminal.cli
```

---

### 3. Windows 🪟 (Adaptable via WSL2)

**Current Status:** Not natively supported, but **works perfectly with WSL2**.

**Recommended: Use WSL2 (Windows Subsystem for Linux)**

#### Step 1: Install WSL2

```bash
# In PowerShell (as Administrator)
wsl --install -d Ubuntu

# Restart your computer
```

#### Step 2: Install iTerminal in WSL2

```bash
# In WSL2 terminal
sudo apt update
sudo apt install python3-pip python3-venv
cd /tmp
git clone <iterminal-repo>
cd iterminal

pip install -r requirements.txt
python -m iterminal.cli
```

**Benefits of WSL2:**
- ✅ Full Linux environment
- ✅ Full iTerminal compatibility
- ✅ Can still run Windows apps
- ✅ Shared file system with Windows

**Alternative: Native Windows Port (Advanced)**

```python
# Would require:
# 1. Replace bash with PowerShell/CMD
# 2. Adapt all Linux commands to Windows equivalents
# 3. Handle Windows-specific paths (C:\Users vs /home)
# 4. Map package managers (apt -> choco or winget)
# 5. Replace /proc filesystem access

# This is significant work but technically possible
```

---

## Porting Guide: Make it Work on Your OS

### For macOS

**File:** `iterminal/os_adapter.py` (create new)

```python
import platform
import subprocess

class OSAdapter:
    """Adapter for OS-specific commands"""
    
    @staticmethod
    def get_os():
        return platform.system()  # "Linux", "Darwin", "Windows"
    
    @staticmethod
    def translate_package_cmd(cmd):
        """Translate package manager commands"""
        os_type = platform.system()
        
        if os_type == "Darwin":  # macOS
            cmd = cmd.replace("apt", "brew")
            cmd = cmd.replace("apt-get", "brew")
            cmd = cmd.replace("systemctl", "launchctl")
        
        return cmd
    
    @staticmethod
    def get_system_info():
        """Get system information"""
        return {
            "os": platform.system(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python": platform.python_version()
        }

# Usage in shell.py
from .os_adapter import OSAdapter

# Before executing command
cmd = OSAdapter.translate_package_cmd(cmd)
```

**Changes Needed in `shell.py`:**

```python
# Add at top
from .os_adapter import OSAdapter

# In execute_shell_command()
def execute_shell_command(cmd, ...):
    # Translate command for current OS
    cmd = OSAdapter.translate_package_cmd(cmd)
    
    # Rest of code...
    return subprocess.run(cmd, shell=True, ...)
```

### For Windows (via WSL2)

**No code changes needed!** Just run in WSL2.

```bash
# Inside WSL2 terminal
python -m iterminal.cli
```

### For Other Unix Systems

Most Unix systems (BSD, OpenBSD, etc.) should work with minor modifications:

```bash
# Key differences:
# 1. Package manager (pkg, apt, brew, etc.)
# 2. Shell location (sh vs bash)
# 3. coreutils location

# Test on your system
python -m iterminal.cli

# If issues, create os_adapter.py as above
```

---

## Environment Variables for OS Adaptation

Add these to `iterminal/config/settings.py`:

```python
@dataclass
class OSConfig:
    """OS-specific configuration"""
    system: str = os.getenv("ITERMINAL_OS_TYPE", platform.system())
    shell: str = os.getenv("ITERMINAL_SHELL", "/bin/bash")
    package_manager: str = os.getenv("ITERMINAL_PKG_MANAGER", "")
    use_sudo: bool = os.getenv("ITERMINAL_USE_SUDO", "true").lower() == "true"
    compatibility_mode: bool = os.getenv("ITERMINAL_COMPAT_MODE", "false").lower() == "true"
```

---

## Compatibility Checklist

| Feature | Linux | macOS | Windows (WSL2) |
|---------|-------|-------|----------------|
| **Core Shell** | ✅ | ⚠️ (needs bash 4) | ✅ |
| **Package Manager** | ✅ | ⚠️ (different PM) | ✅ |
| **File System** | ✅ | ⚠️ (case-insensitive) | ✅ |
| **AI Provider (Ollama)** | ✅ | ✅ | ✅ |
| **AI Provider (OpenRouter)** | ✅ | ✅ | ✅ |
| **Tab Completion** | ✅ | ⚠️ | ✅ |
| **Command Execution** | ✅ | ⚠️ | ✅ |
| **Performance** | ✅ | ✅ | ✅ |

---

## Installation by OS

### Linux (Recommended)

```bash
# 1. Clone and install
git clone <repo>
cd iterminal
pip install -r requirements.txt

# 2. Run
python -m iterminal.cli
```

### macOS

#### Option 1: Docker (Recommended)
```bash
docker run -it python:3.11 bash
# Inside container
pip install git+<iterminal-repo>
iterminal
```

#### Option 2: Native (with GNU tools)
```bash
# Install GNU versions
brew install bash@4 gnu-sed gnu-coreutils

# Update PATH
export PATH="/usr/local/opt/gnu-sed/libexec/gnubin:$PATH"

# Install iTerminal
pip install -r requirements.txt
python -m iterminal.cli
```

### Windows (WSL2)

```powershell
# In PowerShell as Administrator
wsl --install -d Ubuntu
```

```bash
# In WSL2 terminal
sudo apt update
sudo apt install python3-pip
pip install -r requirements.txt
python -m iterminal.cli
```

---

## OS-Specific Issues & Solutions

### macOS Issues

**Issue 1: bash 3.x not compatible**
```bash
# Solution: Use bash 4
brew install bash@4
/usr/local/opt/bash@4/bin/bash
```

**Issue 2: Different sed syntax**
```bash
# Solution: Use gnu-sed
brew install gnu-sed
alias sed=gsed
```

**Issue 3: Package manager differences**
```bash
# Create translation layer in os_adapter.py
apt → brew
systemctl → launchctl
/etc/apt/sources.list → /usr/local/Homebrew/
```

### Windows (WSL2) Issues

**Issue 1: Slow file access across WSL/Windows boundary**
```bash
# Solution: Keep files inside WSL
# ✅ Good:   /home/user/project
# ❌ Slow:   /mnt/c/Users/user/project
```

**Issue 2: Line endings (CRLF vs LF)**
```bash
# Solution: Configure git
git config --global core.autocrlf true
```

### Other Unix Issues

**Issue: Different coreutils location**
```bash
# Solution: Use os_adapter to find commands
which ls  # Find full path
which grep
which sed
```

---

## Future Roadmap

### Phase 1: Current ✅
- Linux support 100%
- Documentation for other OSes

### Phase 2: Planned 🚀
- macOS support (with OS adapter)
- Windows native support (via WSL2 setup wizard)
- BSD support

### Phase 3: Future 🎯
- Native Windows port (PowerShell/CMD)
- Android termux support
- Web-based terminal

---

## Testing Your OS

```bash
# Quick compatibility test
python << 'EOF'
import platform
import subprocess
import shutil

print("=== OS Compatibility Test ===")
print(f"OS: {platform.system()}")
print(f"Python: {platform.python_version()}")
print(f"Shell: {shutil.which('bash')}")

# Test required commands
for cmd in ["bash", "python3", "git", "curl"]:
    path = shutil.which(cmd)
    print(f"{cmd}: {'✅' if path else '❌'} {path or 'NOT FOUND'}")

# Test if Python 3.8+
import sys
version_ok = sys.version_info >= (3, 8)
print(f"Python 3.8+: {'✅' if version_ok else '❌'}")
EOF
```

---

## Summary

| OS | Support | Method | Difficulty |
|-------|---------|--------|------------|
| **Linux** | ✅ Full | Direct | Easy |
| **macOS** | ⚠️ Partial | Docker or Native | Medium |
| **Windows** | ✅ Full (WSL2) | WSL2 | Easy |
| **Other Unix** | ⚠️ Partial | Adapt code | Medium |

**Recommendation:** Start with Linux. If you need macOS/Windows, use Docker or WSL2 for 100% compatibility!

---

## Want to Port iTerminal?

If you want to port iTerminal to your OS:

1. **Fork the repo** and create `iterminal/os_adapter.py`
2. **Implement OS-specific command translation**
3. **Test on your OS** and document issues
4. **Submit PR** with OS adapter
5. **Update documentation** with setup guide

We're happy to help with cross-OS support! 🎉
