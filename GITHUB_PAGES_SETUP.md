# Setting Up GitHub Pages for Oregon Trail Decompiler

This document provides instructions for setting up GitHub Pages to host the Oregon Trail Deluxe documentation website.

## Prerequisites

- A GitHub account
- This repository pushed to GitHub

## Setup Instructions

1. **Push the repository to GitHub**

   If you haven't already, create a repository on GitHub and push this code:

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/oregon-trail-decompiler.git
   git push -u origin main
   ```

2. **Enable GitHub Pages**

   - Go to your repository on GitHub
   - Click on "Settings"
   - Scroll down to the "GitHub Pages" section
   - Under "Source", select "GitHub Actions"
   - The GitHub Actions workflow will automatically deploy the site

3. **Update Repository Information**

   - Edit the following files to replace `yourusername` with your actual GitHub username:
     - `README.md`
     - `docs/_config.yml`
     - `.github/workflows/pages.yml` (if needed)

4. **Wait for Deployment**

   - After pushing changes to the main branch, GitHub Actions will automatically build and deploy the site
   - You can check the status in the "Actions" tab of your repository
   - Once deployed, your site will be available at `https://yourusername.github.io/oregon-trail-decompiler/`

## Structure

The website is deployed from the `docs/` directory, which contains:

- `index.html` - Main documentation page
- `gallery.html` - Image galleries
- `modern/` - All converted assets (images, sounds, music, etc.)
- `.nojekyll` - Tells GitHub Pages not to process the site with Jekyll
- `_config.yml` - Configuration for GitHub Pages

## Updating Assets

When you run `python main.py`, the script will:

1. Clean the `raw_extracted/` and `docs/modern/` directories
2. Extract all files from OREGON.GXL to `raw_extracted/`
3. Convert all game files to modern formats directly in `docs/modern/`

This means that any changes or new assets will be automatically placed in the correct location for GitHub Pages deployment.

## Customization

- To customize the site appearance, edit the HTML and CSS in `index.html` and `gallery.html`
- To update content, modify the HTML files and push the changes to GitHub
- The site will automatically redeploy when changes are pushed to the main branch

## Troubleshooting

If the site doesn't deploy correctly:

1. Check the GitHub Actions logs for errors
2. Ensure all file paths are correct (they should be relative to the repository root)
3. Verify that the `.github/workflows/pages.yml` file is properly configured
4. Make sure the `docs/` directory contains all necessary files

## GitHub Actions Workflow

The GitHub Actions workflow uses the following actions:

- `actions/checkout@v4` - Checks out your repository
- `actions/configure-pages@v4` - Configures GitHub Pages
- `actions/upload-pages-artifact@v3` - Uploads the docs directory as an artifact
- `actions/deploy-pages@v4` - Deploys the artifact to GitHub Pages

These are the latest versions as of April 2025 and should be compatible with GitHub's requirements.