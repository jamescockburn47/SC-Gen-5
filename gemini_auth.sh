#!/bin/bash

# Gemini CLI Authentication Helper for Strategic Counsel Gen 5
# This script helps authenticate with Google Cloud for Gemini API access

echo "🤖 Gemini CLI Authentication Helper"
echo "===================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not found!"
    echo "Please run: ./install_gemini_cli.sh first"
    exit 1
fi

echo "✅ Google Cloud SDK found"

# Check current authentication status
echo ""
echo "🔍 Checking current authentication status..."

if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "✅ Already authenticated!"
    CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    echo "   Account: $CURRENT_ACCOUNT"
    
    # Check project
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [ -n "$CURRENT_PROJECT" ]; then
        echo "   Project: $CURRENT_PROJECT"
        echo ""
        echo "✅ You're all set! You can use Gemini CLI now."
        exit 0
    else
        echo "⚠️  No project set. Let's configure one..."
    fi
else
    echo "❌ Not authenticated"
    echo ""
    echo "Let's get you authenticated! Choose an option:"
    echo ""
    echo "1. 🎯 Application Default Credentials (RECOMMENDED)"
    echo "   Best for development, creates credentials apps can use"
    echo ""
    echo "2. 👤 User Account Login"
    echo "   Traditional user authentication"
    echo ""
    echo "3. 🔧 Manual Setup"
    echo "   I'll show you the commands to run"
    echo ""
    
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo ""
            echo "🎯 Starting Application Default Credentials flow..."
            echo "This will open a URL that you need to copy into your browser."
            echo ""
            gcloud auth application-default login --no-browser
            ;;
        2)
            echo ""
            echo "👤 Starting User Account Login flow..."
            echo "This will open a URL that you need to copy into your browser."
            echo ""
            gcloud auth login --no-browser
            ;;
        3)
            echo ""
            echo "🔧 Manual Setup Instructions:"
            echo ""
            echo "Run one of these commands in your terminal:"
            echo ""
            echo "Option A (Recommended):"
            echo "  gcloud auth application-default login --no-browser"
            echo ""
            echo "Option B:"
            echo "  gcloud auth login --no-browser"
            echo ""
            echo "Both will show you a URL to copy into your browser."
            echo "After authentication, run this script again to continue setup."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

# Check if authentication was successful
echo ""
echo "🔍 Verifying authentication..."

if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "✅ Authentication successful!"
    CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    echo "   Account: $CURRENT_ACCOUNT"
else
    echo "❌ Authentication failed. Please try again."
    exit 1
fi

# Project setup
echo ""
echo "🔧 Setting up Google Cloud project..."

CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)

if [ -n "$CURRENT_PROJECT" ]; then
    echo "✅ Project already set: $CURRENT_PROJECT"
else
    echo "No project configured. Let's set one up:"
    echo ""
    echo "Options:"
    echo "1. 🆕 Create a new project"
    echo "2. 📋 List existing projects and choose one"
    echo "3. ⌨️  Enter project ID manually"
    echo ""
    
    read -p "Choose option (1-3): " project_choice
    
    case $project_choice in
        1)
            read -p "Enter new project ID (lowercase, numbers, hyphens only): " new_project_id
            echo "Creating project: $new_project_id"
            gcloud projects create "$new_project_id"
            gcloud config set project "$new_project_id"
            CURRENT_PROJECT="$new_project_id"
            ;;
        2)
            echo ""
            echo "📋 Your available projects:"
            gcloud projects list
            echo ""
            read -p "Enter project ID from the list above: " selected_project
            gcloud config set project "$selected_project"
            CURRENT_PROJECT="$selected_project"
            ;;
        3)
            read -p "Enter project ID: " manual_project
            gcloud config set project "$manual_project"
            CURRENT_PROJECT="$manual_project"
            ;;
        *)
            echo "Invalid choice. Skipping project setup."
            ;;
    esac
fi

# Enable required APIs
if [ -n "$CURRENT_PROJECT" ]; then
    echo ""
    echo "🔌 Enabling required APIs..."
    
    echo "Enabling Vertex AI API..."
    gcloud services enable aiplatform.googleapis.com --project="$CURRENT_PROJECT"
    
    echo "Enabling ML API..."
    gcloud services enable ml.googleapis.com --project="$CURRENT_PROJECT"
    
    echo "✅ APIs enabled successfully!"
fi

# Final status check
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "✅ Authenticated as: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
echo "✅ Project: $(gcloud config get-value project)"
echo "✅ APIs: Enabled"
echo ""
echo "🚀 You can now use Gemini CLI in Strategic Counsel Gen 5!"
echo ""
echo "Next steps:"
echo "1. Go to the Streamlit UI: http://localhost:8501"
echo "2. Click on the '🤖 Gemini CLI' tab"
echo "3. Start analyzing your repository or chatting with Gemini!"
echo ""
echo "Need help? Check the documentation or run: gcloud auth list" 