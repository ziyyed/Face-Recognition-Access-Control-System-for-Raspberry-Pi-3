# GitHub Setup Instructions

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the **"+"** icon → **"New repository"**
3. Repository name: `Face_Detection_System` (or any name you prefer)
4. Description: "Face Recognition Access Control System for Raspberry Pi 3"
5. Choose **Public** or **Private**
6. **DO NOT** initialize with README, .gitignore, or license (we already have these)
7. Click **"Create repository"**

## Step 2: Push to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/Face_Detection_System.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Alternative: Using SSH

If you have SSH keys set up:

```bash
git remote add origin git@github.com:YOUR_USERNAME/Face_Detection_System.git
git branch -M main
git push -u origin main
```

## Update Git User Info (Optional)

If you want to change the git user info:

```bash
# For this repository only
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Or globally for all repositories
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Future Updates

After making changes:

```bash
git add .
git commit -m "Description of changes"
git push
```


