"""
Pre-cached responses for common Git commands to reduce AI query latency
"""

GIT_COMMAND_CACHE = {
    "git": """
Git is a distributed version control system used to track changes in source code during software development.

Usage: git [--version] [--help] [-C <path>] [-c <name>=<value>]
           [--exec-path[=<path>]] [--html-path] [--man-path] [--info-path]
           [-p | --paginate | -P | --no-pager] [--no-replace-objects] [--bare]
           [--git-dir=<path>] [--work-tree=<path>] [--namespace=<name>]
           [--super-prefix=<path>] [--config-env=<name>=<envvar>]
           <command> [<args>]

Common Git commands:
   add        Add file contents to the index
   branch     List, create, or delete branches
   checkout   Switch branches or restore working tree files
   clone      Clone a repository into a new directory
   commit     Record changes to the repository
   diff       Show changes between commits, commit and working tree, etc
   fetch      Download objects and refs from another repository
   init       Create an empty Git repository or reinitialize an existing one
   log        Show commit logs
   merge      Join two or more development histories together
   pull       Fetch from and integrate with another repository or a local branch
   push       Update remote refs along with associated objects
   rebase     Reapply commits on top of another base tip
   reset      Reset current HEAD to the specified state
   restore    Restore working tree files
   status     Show the working tree status
""",
    
    "git status": """
Git status shows the state of the working directory and the staging area.
It lets you see which changes have been staged, which haven't, and which files aren't being tracked by Git.

This command displays:
- Changes that have been staged and are ready to be committed
- Changes that have been made but not yet staged
- Untracked files (new files that Git doesn't yet track)

Common output sections:
1. "Changes to be committed" - Changes that have been staged (git add)
2. "Changes not staged for commit" - Modified tracked files not yet staged
3. "Untracked files" - New files not yet tracked by Git
""",
    
    "git add": """
The git add command adds new or changed files in your working directory to the Git staging area.

Usage: git add [file(s)]

Common options:
  -A, --all       Stage all files (modified, new, and deleted)
  -u, --update    Stage modified and deleted files only (not new ones)
  -p, --patch     Interactively choose hunks to stage
  
Examples:
  git add file.txt       # Stage a specific file
  git add .              # Stage all files in current directory
  git add -A             # Stage all changes in the repo
  git add src/*.js       # Stage all JavaScript files in src folder
""",
    
    "git commit": """
The git commit command captures a snapshot of the project's currently staged changes.

Usage: git commit [options]

Common options:
  -m, --message    Add a commit message
  -a, --all        Automatically stage and commit all modified files
  --amend          Modify the most recent commit
  
Examples:
  git commit -m "Fix bug in login form"    # Commit with message
  git commit -am "Update documentation"     # Stage modified files and commit
  git commit --amend                        # Modify last commit
""",
    
    "git push": """
The git push command uploads local repository commits to a remote repository.

Usage: git push [remote] [branch]

Common options:
  -u, --set-upstream    Set upstream reference for current branch
  --force               Force push (use with caution!)
  --tags                Push all tags
  
Examples:
  git push                      # Push to default remote (usually origin)
  git push origin main          # Push local main branch to origin/main
  git push -u origin feature    # Push and set upstream for tracking
  git push --tags               # Push all local tags
""",
    
    "git pull": """
The git pull command fetches changes from a remote repository and integrates them into the current branch.
It's equivalent to running git fetch followed by git merge.

Usage: git pull [remote] [branch]

Common options:
  --rebase               Rebase instead of merge
  --no-commit            Don't commit the merge
  --ff-only              Fast-forward only (abort if not possible)
  
Examples:
  git pull                     # Pull from default remote into current branch
  git pull origin main         # Pull from origin/main into current branch
  git pull --rebase            # Pull and rebase instead of merge
""",
    
    "git clone": """
The git clone command creates a copy of an existing Git repository.

Usage: git clone [repository URL] [directory]

Common options:
  --depth        Create a shallow clone with limited history
  --branch, -b   Clone a specific branch
  --recursive    Clone submodules recursively
  
Examples:
  git clone https://github.com/username/repo.git           # Clone a repository
  git clone https://github.com/username/repo.git my-repo   # Clone to specific folder
  git clone --branch dev https://github.com/username/repo.git  # Clone specific branch
  git clone --depth 1 https://github.com/username/repo.git     # Shallow clone
""",
    
    "git branch": """
The git branch command lets you create, list, rename, and delete branches.

Usage: git branch [options] [branch name]

Common options:
  -a, --all            List all branches (local and remote)
  -r, --remotes        List remote branches
  -d, --delete         Delete a branch
  -m, --move           Rename a branch
  -v, --verbose        Show commit SHA and subject line
  
Examples:
  git branch                    # List local branches
  git branch -a                 # List all branches
  git branch feature            # Create a new branch called 'feature'
  git branch -d feature         # Delete the branch 'feature'
  git branch -m old-name new-name  # Rename branch
""",
    
    "git checkout": """
The git checkout command is used to switch between branches or restore working tree files.

Usage: git checkout [options] <branch name or file>

Common options:
  -b                Create and switch to a new branch
  -B                Create/reset and switch to a branch
  -f, --force       Force checkout (throw away local changes)
  
Examples:
  git checkout main                  # Switch to main branch
  git checkout -b feature            # Create and switch to a new branch
  git checkout -- file.txt           # Restore a file from the index
  git checkout HEAD~2 file.txt       # Restore a file from 2 commits ago
""",
    
    "git merge": """
The git merge command incorporates changes from another branch into the current branch.

Usage: git merge [options] <branch>

Common options:
  --no-ff               Always create a merge commit
  --squash              Squash all commits into one commit
  --abort               Abort the current merge process
  
Examples:
  git merge feature              # Merge feature branch into current branch
  git merge --no-ff feature      # Merge with a merge commit
  git merge --squash feature     # Merge and squash all commits
  git merge --abort              # Abort an in-progress merge
""",
    
    "git log": """
The git log command shows the commit history of a repository.

Usage: git log [options]

Common options:
  --oneline          Show each commit on one line
  -n <number>        Show only the last n commits
  --graph            Display ASCII graph of branch and merge history
  --stat             Show stats for files modified in each commit
  --author=<pattern> Filter commits by author
  
Examples:
  git log                     # Show commit history
  git log --oneline           # Show compact commit history
  git log --graph --oneline   # Show graphical commit history
  git log -n 5                # Show only the last 5 commits
  git log --author="John"     # Show commits by author matching "John"
""",
    
    "git reset": """
The git reset command resets the current HEAD to a specified state.

Usage: git reset [options] [commit]

Common options:
  --soft            Only reset HEAD pointer
  --mixed           Reset HEAD and index (default)
  --hard            Reset HEAD, index, and working directory
  
Examples:
  git reset --soft HEAD~1     # Undo last commit, keep changes staged
  git reset HEAD~1            # Undo last commit, keep changes unstaged
  git reset --hard HEAD~1     # Undo last commit, discard all changes
  git reset --hard origin/main # Reset to match remote main branch
""",
    
    "git fetch": """
The git fetch command downloads objects and refs from another repository.
Unlike pull, fetch does not merge changes into your current branch.

Usage: git fetch [options] [remote] [branch]

Common options:
  --all               Fetch all remotes
  -p, --prune         Remove remote-tracking branches that no longer exist
  -t, --tags          Fetch all tags
  
Examples:
  git fetch                  # Update from default remote
  git fetch origin           # Update from origin remote
  git fetch origin main      # Update specific branch from origin
  git fetch --all            # Update from all remotes
  git fetch --prune          # Update and clean up stale branches
""",
    
    "git rebase": """
The git rebase command reapplies commits on top of another base.

Usage: git rebase [options] [base]

Common options:
  -i, --interactive    Interactive rebase
  --onto <newbase>     Rebase onto a different branch
  --abort              Abort current rebase
  --continue           Continue rebase after resolving conflicts
  
Examples:
  git rebase main                # Rebase current branch onto main
  git rebase -i HEAD~3           # Interactive rebase for last 3 commits
  git rebase --onto main feature # Rebase feature branch onto main
  git rebase --abort             # Abort an in-progress rebase
""",
}