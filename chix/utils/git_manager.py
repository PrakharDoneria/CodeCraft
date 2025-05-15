"""
Git integration for ChiX Editor
Handles git operations like status, commit, push, etc.
"""

import os
import subprocess
import re
from pathlib import Path

class GitManager:
    """Handles Git operations for a repository"""
    
    def __init__(self, repo_path=None):
        """
        Initialize GitManager with a repository path
        
        Args:
            repo_path (str, optional): Path to the git repository. If None, tries to detect it.
        """
        self.repo_path = repo_path
        if not self.repo_path:
            self.repo_path = self._detect_repo_path()
    
    def _detect_repo_path(self, start_path=None):
        """
        Detect git repository by walking up from current directory
        
        Args:
            start_path (str, optional): Path to start searching from. If None, uses current directory.
            
        Returns:
            str: Path to repository or None if not found
        """
        if not start_path:
            start_path = os.getcwd()
            
        path = Path(start_path)
        
        # Walk up directories
        while True:
            # Check if .git exists in this directory
            git_dir = path / '.git'
            if git_dir.exists() and git_dir.is_dir():
                return str(path)
                
            # Stop if we've reached the root
            if path.parent == path:
                return None
                
            # Go up one level
            path = path.parent
    
    def is_git_repo(self):
        """
        Check if current directory is a git repository
        
        Returns:
            bool: True if current directory is a git repository
        """
        if not self.repo_path:
            return False
            
        git_dir = os.path.join(self.repo_path, '.git')
        return os.path.exists(git_dir) and os.path.isdir(git_dir)
    
    def _run_git_command(self, command, cwd=None):
        """
        Run a git command and return the result
        
        Args:
            command (list): Git command parts
            cwd (str, optional): Working directory
            
        Returns:
            (int, str): (return code, output) tuple
        """
        if not cwd:
            cwd = self.repo_path
            
        try:
            full_command = ['git'] + command
            process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=cwd,
                universal_newlines=True
            )
            output, _ = process.communicate()
            return process.returncode, output
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            return 1, str(e)
    
    def get_status(self):
        """
        Get git status information
        
        Returns:
            dict: Status information dictionary
        """
        if not self.is_git_repo():
            return {"error": "Not a git repository"}
            
        status_info = {
            "modified": [],
            "untracked": [],
            "staged": [],
            "deleted": [],
            "renamed": [],
            "branch": "unknown",
            "is_clean": True
        }
        
        # Get current branch
        code, output = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
        if code == 0:
            status_info["branch"] = output.strip()
        
        # Get status
        code, output = self._run_git_command(['status', '--porcelain', '--branch'])
        if code != 0:
            return {"error": output}
            
        # Parse the status output
        for line in output.splitlines():
            if line.startswith('##'):
                # Branch information
                continue
                
            if len(line) < 2:
                continue
                
            status_code = line[:2]
            file_path = line[3:].strip()
            
            # Skip spaces in the status output
            if not file_path:
                continue
                
            # Handle renamed files
            if status_code[0] == 'R' or status_code[1] == 'R':
                parts = file_path.split(' -> ')
                if len(parts) == 2:
                    file_path = parts[1]  # Use the new name
                status_info["renamed"].append(file_path)
                status_info["is_clean"] = False
                continue
                
            # Handle status codes
            if status_code[0] != ' ' and status_code[0] != '?':
                # Staged changes
                status_info["staged"].append(file_path)
                status_info["is_clean"] = False
                
            if status_code[0] == 'D' or status_code[1] == 'D':
                # Deleted files
                status_info["deleted"].append(file_path)
                status_info["is_clean"] = False
            elif status_code[1] == 'M':
                # Modified files
                status_info["modified"].append(file_path)
                status_info["is_clean"] = False
            elif status_code[0] == '?':
                # Untracked files
                status_info["untracked"].append(file_path)
                status_info["is_clean"] = False
        
        return status_info
    
    def get_file_status(self, file_path):
        """
        Get the git status of a specific file
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: Status string ('modified', 'untracked', 'staged', 'deleted', 'renamed', or None)
        """
        if not self.is_git_repo():
            return None
            
        # Make relative to repository if needed
        if os.path.isabs(file_path) and self.repo_path:
            rel_path = os.path.relpath(file_path, self.repo_path)
            if rel_path.startswith('..'):
                # File is outside the repository
                return None
            file_path = rel_path
            
        # Get status info
        status = self.get_status()
        
        if file_path in status.get("modified", []):
            return "modified"
        elif file_path in status.get("untracked", []):
            return "untracked"
        elif file_path in status.get("staged", []):
            return "staged"
        elif file_path in status.get("deleted", []):
            return "deleted"
        elif file_path in status.get("renamed", []):
            return "renamed"
            
        return None
    
    def commit(self, message):
        """
        Commit staged changes
        
        Args:
            message (str): Commit message
            
        Returns:
            (bool, str): (success, message) tuple
        """
        if not self.is_git_repo():
            return False, "Not a git repository"
            
        code, output = self._run_git_command(['commit', '-m', message])
        return code == 0, output
    
    def stage_file(self, file_path):
        """
        Stage a file for commit
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            (bool, str): (success, message) tuple
        """
        if not self.is_git_repo():
            return False, "Not a git repository"
            
        code, output = self._run_git_command(['add', file_path])
        return code == 0, output
    
    def unstage_file(self, file_path):
        """
        Unstage a file
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            (bool, str): (success, message) tuple
        """
        if not self.is_git_repo():
            return False, "Not a git repository"
            
        code, output = self._run_git_command(['reset', 'HEAD', file_path])
        return code == 0, output
    
    def get_current_branch(self):
        """
        Get the current branch name
        
        Returns:
            str: Current branch name or None if not in a git repository
        """
        if not self.is_git_repo():
            return None
            
        code, output = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
        if code == 0:
            return output.strip()
        return None
    
    def get_branches(self):
        """
        Get list of all branches
        
        Returns:
            list: List of branch names
        """
        if not self.is_git_repo():
            return []
            
        code, output = self._run_git_command(['branch'])
        if code == 0:
            branches = []
            for line in output.splitlines():
                line = line.strip()
                if line.startswith('*'):
                    # Current branch
                    branches.append(line[2:].strip())
                else:
                    branches.append(line.strip())
            return branches
        return []
    
    def switch_branch(self, branch_name):
        """
        Switch to another branch
        
        Args:
            branch_name (str): Name of the branch to switch to
            
        Returns:
            (bool, str): (success, message) tuple
        """
        if not self.is_git_repo():
            return False, "Not a git repository"
            
        code, output = self._run_git_command(['checkout', branch_name])
        return code == 0, output
    
    def create_branch(self, branch_name):
        """
        Create a new branch
        
        Args:
            branch_name (str): Name of the new branch
            
        Returns:
            (bool, str): (success, message) tuple
        """
        if not self.is_git_repo():
            return False, "Not a git repository"
            
        code, output = self._run_git_command(['checkout', '-b', branch_name])
        return code == 0, output
    
    def get_commit_history(self, max_count=10):
        """
        Get commit history
        
        Args:
            max_count (int): Maximum number of commits to return
            
        Returns:
            list: List of commit dictionaries
        """
        if not self.is_git_repo():
            return []
            
        code, output = self._run_git_command([
            'log', 
            f'--max-count={max_count}', 
            '--pretty=format:%H|%an|%ad|%s', 
            '--date=short'
        ])
        
        if code == 0:
            commits = []
            for line in output.splitlines():
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commit = {
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    }
                    commits.append(commit)
            return commits
        return []