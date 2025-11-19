# How to Pull Changes from GitHub on CentOS 8 Linux

This guide shows you how to pull the latest changes from the Suntech repository on CentOS 8.

## Prerequisites

- The repository must already be cloned (see `CLONE_INSTRUCTIONS.md`)
- Git must be installed
- You must have internet connectivity

## Quick Pull Command

If you're already in the repository directory:

```bash
git pull origin main
```

## Step-by-Step Instructions

### Step 1: Navigate to the Repository Directory

```bash
# If you cloned to your home directory
cd ~/Suntech

# Or if you cloned to a different location
cd /path/to/Suntech
```

### Step 2: Check Current Status

Before pulling, check what branch you're on and if you have any local changes:

```bash
# Check current branch
git branch

# Check status (shows uncommitted changes)
git status

# See recent commits
git log --oneline -5
```

### Step 3: Pull the Latest Changes

**Option A: Simple Pull (Recommended)**
```bash
git pull origin main
```

**Option B: Pull with Rebase (Cleaner history)**
```bash
git pull --rebase origin main
```

**Option C: Fetch then Merge (More control)**
```bash
# First, fetch changes without merging
git fetch origin main

# See what will be merged
git log HEAD..origin/main

# Then merge
git merge origin/main
```

### Step 4: Verify the Pull

After pulling, verify the changes:

```bash
# Check latest commits
git log --oneline -5

# Check current status
git status

# See what files changed
git diff HEAD~1 HEAD
```

## Complete Example Session

```bash
# 1. Navigate to repository
cd ~/Suntech

# 2. Check current status
git status

# 3. Pull latest changes
git pull origin main

# 4. Verify
git log --oneline -3
```

## Handling Common Scenarios

### Scenario 1: You Have Local Uncommitted Changes

If you have local changes that haven't been committed:

```bash
# Option A: Stash your changes, pull, then reapply
git stash
git pull origin main
git stash pop

# Option B: Commit your changes first
git add .
git commit -m "Your local changes"
git pull origin main
```

### Scenario 2: Merge Conflicts

If there are conflicts between local and remote changes:

```bash
# Pull will show conflicts
git pull origin main

# View conflicted files
git status

# Edit conflicted files manually
# Look for conflict markers: <<<<<<< ======= >>>>>>>

# After resolving conflicts:
git add <resolved-files>
git commit -m "Resolve merge conflicts"

# Or abort the merge
git merge --abort
```

### Scenario 3: Local Commits Ahead of Remote

If you have local commits that aren't on GitHub:

```bash
# See what commits are local only
git log origin/main..HEAD

# Push your local commits first
git push origin main

# Then pull (should be up to date)
git pull origin main
```

### Scenario 4: Repository is Behind

If you want to see how many commits behind you are:

```bash
# Fetch without merging
git fetch origin main

# See commits you're missing
git log HEAD..origin/main --oneline

# See how many commits behind
git rev-list --count HEAD..origin/main
```

## Updating to Latest Version Script

Create a simple script to update:

```bash
#!/bin/bash
# update_suntech.sh

cd ~/Suntech || exit 1
echo "Pulling latest changes from GitHub..."
git pull origin main
if [ $? -eq 0 ]; then
    echo "Successfully updated!"
    git log --oneline -3
else
    echo "Error pulling changes. Check for conflicts."
fi
```

Make it executable:
```bash
chmod +x update_suntech.sh
./update_suntech.sh
```

## Setting Up Auto-Pull (Optional)

### Method 1: Cron Job

Set up a cron job to automatically pull changes:

```bash
# Edit crontab
crontab -e

# Add this line to pull every hour (adjust path as needed)
0 * * * * cd /home/username/Suntech && git pull origin main >> /tmp/git_pull.log 2>&1
```

### Method 2: Git Hook (Post-Receive)

If you want to auto-update when changes are pushed:

```bash
# Create a post-receive hook (advanced)
# This is typically used on the server side
```

## Troubleshooting

### Issue: "fatal: not a git repository"

**Solution:** Make sure you're in the repository directory:
```bash
cd ~/Suntech
# or wherever you cloned it
```

### Issue: "error: Your local changes would be overwritten by merge"

**Solution:** Stash or commit your changes first:
```bash
git stash
git pull origin main
git stash pop
```

### Issue: "fatal: refusing to merge unrelated histories"

**Solution:** This happens when local and remote have different histories:
```bash
git pull origin main --allow-unrelated-histories
```

### Issue: "Permission denied (publickey)"

**Solution:** Use HTTPS instead of SSH, or set up SSH keys:
```bash
# Check remote URL
git remote -v

# Change to HTTPS if using SSH
git remote set-url origin https://github.com/shafiqnik/Suntech.git
```

### Issue: "fatal: unable to access 'https://github.com/...': SSL certificate problem"

**Solution:** Update CA certificates:
```bash
sudo yum update ca-certificates -y
# or
sudo dnf update ca-certificates -y
```

### Issue: Network connectivity problems

**Solution:** Check connectivity:
```bash
# Test GitHub connectivity
ping github.com

# Test DNS
nslookup github.com

# Check firewall
sudo firewall-cmd --list-all
```

## Best Practices

1. **Always check status before pulling:**
   ```bash
   git status
   ```

2. **Pull regularly to stay up to date:**
   ```bash
   git pull origin main
   ```

3. **Review changes before pulling:**
   ```bash
   git fetch origin main
   git log HEAD..origin/main
   git pull origin main
   ```

4. **Keep a backup of important local changes:**
   ```bash
   git stash save "backup before pull"
   git pull origin main
   ```

5. **Use descriptive commit messages if you make local changes:**
   ```bash
   git commit -m "Local configuration changes"
   ```

## Quick Reference Commands

```bash
# Pull latest changes
git pull origin main

# Check what will be pulled
git fetch origin main
git log HEAD..origin/main

# See current status
git status

# View recent commits
git log --oneline -10

# View changes in last pull
git diff HEAD~1 HEAD

# Reset to match remote (WARNING: loses local changes)
git fetch origin main
git reset --hard origin/main
```

## Repository Information

- **Repository URL:** https://github.com/shafiqnik/Suntech
- **Default Branch:** main
- **Remote Name:** origin

## Additional Resources

- See `CLONE_INSTRUCTIONS.md` for initial setup
- See `README.md` for project documentation
- GitHub Help: https://docs.github.com/en/get-started/getting-started-with-git

