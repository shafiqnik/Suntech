# How to Clone Suntech Repository on CentOS 8 Linux

This guide provides step-by-step instructions to clone the Suntech repository on CentOS 8.

## Prerequisites

### Step 1: Install Git (if not already installed)

Check if git is installed:
```bash
git --version
```

If git is not installed, install it using one of these methods:

**Option A: Using yum (CentOS 8 default)**
```bash
sudo yum install git -y
```

**Option B: Using dnf (recommended for CentOS 8)**
```bash
sudo dnf install git -y
```

### Step 2: Verify Git Installation
```bash
git --version
```
You should see output like: `git version 2.x.x`

## Cloning the Repository

### Step 3: Navigate to Your Desired Directory

Choose where you want to clone the repository:
```bash
# Option 1: Clone to your home directory
cd ~

# Option 2: Clone to a specific projects directory
mkdir -p ~/projects
cd ~/projects

# Option 3: Clone to /opt (requires sudo)
cd /opt
```

### Step 4: Clone the Repository

**For Public Repository (HTTPS - Recommended):**
```bash
git clone https://github.com/shafiqnik/Suntech.git
```

**For Private Repository (if you have SSH keys set up):**
```bash
git clone git@github.com:shafiqnik/Suntech.git
```

### Step 5: Navigate into the Cloned Directory
```bash
cd Suntech
```

### Step 6: Verify the Clone

List the files to verify everything was cloned:
```bash
ls -la
```

You should see:
- `main.py`
- `server.py`
- `suntech_parser.py`
- `web_server.py`
- `templates/`
- `README.md`
- `.gitignore`
- `requirements.txt`
- And other project files

### Step 7: Check Repository Status
```bash
git status
```

You should see: `On branch main` and `Your branch is up to date with 'origin/main'`

## Complete Example Session

Here's a complete example of cloning the repository:

```bash
# 1. Install git (if needed)
sudo dnf install git -y

# 2. Navigate to home directory
cd ~

# 3. Clone the repository
git clone https://github.com/shafiqnik/Suntech.git

# 4. Enter the repository directory
cd Suntech

# 5. List files
ls -la

# 6. View the README
cat README.md

# 7. Check git status
git status
```

## Setting Up the Application

After cloning, you can set up and run the application:

### Step 8: Verify Python is Installed
```bash
python3 --version
# or
python --version
```

### Step 9: Run the Application
```bash
python3 main.py
```

The application will:
- Start socket server on port **18160**
- Start web server on port **8080**

Access the web interface at: `http://localhost:8080` or `http://your-server-ip:8080`

## Troubleshooting

### Issue: "git: command not found"
**Solution:** Install git using the commands in Step 1

### Issue: "Permission denied" when cloning
**Solution:** 
- Check directory permissions: `ls -ld ~`
- Use a directory you have write access to
- Or use sudo (not recommended for home directory)

### Issue: "fatal: unable to access 'https://github.com/...': SSL certificate problem"
**Solution:**
```bash
# Update CA certificates
sudo yum update ca-certificates -y
# or
sudo dnf update ca-certificates -y
```

### Issue: "fatal: repository 'Suntech' not found"
**Solution:**
- Verify the repository URL is correct: https://github.com/shafiqnik/Suntech
- Check if the repository is private (you'll need authentication)
- Ensure you have internet connectivity: `ping github.com`

### Issue: Need to clone with authentication (private repo)
**Solution:**
1. Generate a Personal Access Token on GitHub
2. Use it as password when prompted:
```bash
git clone https://github.com/shafiqnik/Suntech.git
# Username: shafiqnik
# Password: [your-personal-access-token]
```

Or set up SSH keys:
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key and add to GitHub
cat ~/.ssh/id_ed25519.pub
# Then add this key to GitHub: Settings > SSH and GPG keys
```

## Updating the Repository

To get the latest changes after cloning:

```bash
cd ~/Suntech  # or wherever you cloned it
git pull origin main
```

## Additional Git Configuration (Optional)

Set up your git identity:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Repository Information

- **Repository URL:** https://github.com/shafiqnik/Suntech
- **Branch:** main
- **Language:** Python (51.5%), HTML (44.2%), PowerShell (4.3%)

## Quick Reference

```bash
# One-liner to clone and enter directory
git clone https://github.com/shafiqnik/Suntech.git && cd Suntech
```



