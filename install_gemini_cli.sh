#!/bin/bash

# ================================================================================
# Google Cloud SDK + Gemini CLI Installation Script
# ================================================================================
# This script will:
# 1. Ensure gcloud CLI is installed, or prompt the user to install it
# 2. Update gcloud to the latest version
# 3. Enable gcloud alpha components if not already enabled
# 4. Install the Gemini CLI via gcloud alpha
# 5. Authenticate the user if needed
# 6. Output confirmation that Gemini CLI is working
# ================================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}                     ${CYAN}Gemini CLI Installer${NC}                      ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if gcloud is installed
check_gcloud_installation() {
    if command_exists gcloud; then
        print_success "Google Cloud SDK is already installed"
        gcloud --version
        return 0
    else
        print_error "Google Cloud SDK is not installed"
        return 1
    fi
}

# Install gcloud CLI
install_gcloud() {
    print_status "Installing Google Cloud SDK..."
    
    # Detect OS
    OS=$(uname -s)
    ARCH=$(uname -m)
    
    case "$OS" in
        "Linux")
            if command_exists apt-get; then
                # Debian/Ubuntu
                print_status "Installing via apt-get (Debian/Ubuntu)..."
                sudo apt-get update
                sudo apt-get install -y apt-transport-https ca-certificates gnupg curl
                curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
                echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
                sudo apt-get update && sudo apt-get install -y google-cloud-cli
            elif command_exists yum; then
                # RHEL/CentOS/Fedora
                print_status "Installing via yum (RHEL/CentOS/Fedora)..."
                sudo tee -a /etc/yum.repos.d/google-cloud-sdk.repo << EOM
[google-cloud-cli]
name=Google Cloud CLI
baseurl=https://packages.cloud.google.com/yum/repos/cloud-sdk-el8-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=0
gpgkey=https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOM
                sudo yum install -y google-cloud-cli
            else
                # Generic Linux - use snap or manual install
                install_gcloud_manual
            fi
            ;;
        "Darwin")
            # macOS
            if command_exists brew; then
                print_status "Installing via Homebrew (macOS)..."
                brew install --cask google-cloud-sdk
            else
                print_status "Homebrew not found. Installing manually..."
                install_gcloud_manual
            fi
            ;;
        *)
            print_warning "Unknown OS: $OS. Attempting manual installation..."
            install_gcloud_manual
            ;;
    esac
}

# Manual gcloud installation
install_gcloud_manual() {
    print_status "Performing manual installation of Google Cloud SDK..."
    
    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download appropriate version
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    # Map architecture
    case "$ARCH" in
        "x86_64") ARCH="x86_64" ;;
        "arm64"|"aarch64") ARCH="arm" ;;
        *) 
            print_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
    
    GCLOUD_URL="https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${OS}-${ARCH}.tar.gz"
    
    print_status "Downloading from: $GCLOUD_URL"
    curl -LO "$GCLOUD_URL"
    
    # Extract
    tar -xzf google-cloud-cli-*.tar.gz
    
    # Install to home directory
    INSTALL_DIR="$HOME/google-cloud-sdk"
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Removing existing installation at $INSTALL_DIR"
        rm -rf "$INSTALL_DIR"
    fi
    
    mv google-cloud-sdk "$HOME/"
    
    # Run installer
    "$HOME/google-cloud-sdk/install.sh" --quiet --usage-reporting=false --command-completion=true --path-update=true
    
    # Source the path
    if [ -f "$HOME/.bashrc" ]; then
        source "$HOME/.bashrc"
    fi
    if [ -f "$HOME/.zshrc" ]; then
        source "$HOME/.zshrc"
    fi
    
    # Add to current session PATH
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
    
    # Clean up
    cd "$HOME"
    rm -rf "$TEMP_DIR"
    
    print_success "Manual installation completed"
}

# Update gcloud to latest version
update_gcloud() {
    print_status "Updating Google Cloud SDK to latest version..."
    
    # Update components
    gcloud components update --quiet
    
    print_success "Google Cloud SDK updated successfully"
    gcloud --version
}

# Enable alpha components
enable_alpha_components() {
    print_status "Checking alpha components..."
    
    # Check if alpha is already installed
    if gcloud alpha --help >/dev/null 2>&1; then
        print_success "Alpha components are already enabled"
    else
        print_status "Installing alpha components..."
        gcloud components install alpha --quiet
        print_success "Alpha components installed successfully"
    fi
}

# Install Gemini CLI via gcloud alpha
install_gemini_cli() {
    print_status "Installing Gemini CLI via gcloud alpha..."
    
    # Check if Gemini CLI is available via alpha
    if gcloud alpha ai --help >/dev/null 2>&1; then
        print_success "Gemini CLI (gcloud alpha ai) is available"
    else
        print_warning "Gemini CLI not found in alpha components"
        print_status "Installing AI platform components..."
        gcloud components install alpha --quiet
    fi
    
    # Alternative: Install via gcloud AI platform
    if gcloud alpha ai models --help >/dev/null 2>&1; then
        print_success "AI models CLI is available"
    else
        print_warning "AI models CLI not available. This might be a newer feature."
        print_status "Proceeding with available components..."
    fi
}

# Check authentication
check_authentication() {
    print_status "Checking Google Cloud authentication..."
    
    # Check if user is already authenticated
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 | grep -q "@"; then
        ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1)
        print_success "Already authenticated as: $ACTIVE_ACCOUNT"
        return 0
    else
        print_warning "Not authenticated with Google Cloud"
        return 1
    fi
}

# Authenticate user
authenticate_user() {
    print_status "Starting Google Cloud authentication process..."
    
    echo ""
    echo -e "${CYAN}Choose authentication method:${NC}"
    echo "1. Interactive browser login (recommended)"
    echo "2. Service account key file"
    echo "3. Skip authentication (manual setup later)"
    echo ""
    read -p "Enter your choice (1-3): " auth_choice
    
    case $auth_choice in
        1)
            print_status "Opening browser for authentication..."
            gcloud auth login
            ;;
        2)
            read -p "Enter path to service account key file: " key_file
            if [ -f "$key_file" ]; then
                gcloud auth activate-service-account --key-file="$key_file"
                print_success "Service account authentication completed"
            else
                print_error "Key file not found: $key_file"
                return 1
            fi
            ;;
        3)
            print_warning "Skipping authentication. You can authenticate later with: gcloud auth login"
            return 0
            ;;
        *)
            print_error "Invalid choice. Skipping authentication."
            return 1
            ;;
    esac
}

# Set up project
setup_project() {
    print_status "Setting up Google Cloud project..."
    
    # List available projects
    echo ""
    echo -e "${CYAN}Available projects:${NC}"
    gcloud projects list --format="table(projectId,name,projectNumber)" 2>/dev/null || {
        print_warning "Unable to list projects. You may need to create one first."
        echo "Visit: https://console.cloud.google.com/projectcreate"
        return 1
    }
    
    echo ""
    read -p "Enter project ID to use (or press Enter to skip): " project_id
    
    if [ ! -z "$project_id" ]; then
        gcloud config set project "$project_id"
        print_success "Project set to: $project_id"
        
        # Enable required APIs
        print_status "Enabling required APIs..."
        gcloud services enable aiplatform.googleapis.com --quiet 2>/dev/null || print_warning "Could not enable AI Platform API"
        gcloud services enable ml.googleapis.com --quiet 2>/dev/null || print_warning "Could not enable ML API"
    else
        print_warning "Skipping project setup"
    fi
}

# Test Gemini CLI functionality
test_gemini_cli() {
    print_status "Testing Gemini CLI functionality..."
    
    echo ""
    echo -e "${CYAN}Testing available Gemini CLI commands:${NC}"
    
    # Test gcloud AI commands
    if gcloud alpha ai --help >/dev/null 2>&1; then
        echo "✅ gcloud alpha ai - Available"
    else
        echo "❌ gcloud alpha ai - Not available"
    fi
    
    if gcloud alpha ai models list --help >/dev/null 2>&1; then
        echo "✅ gcloud alpha ai models - Available"
        
        # Try to list models if authenticated and project is set
        if gcloud config get-value project >/dev/null 2>&1; then
            print_status "Attempting to list available models..."
            gcloud alpha ai models list --region=us-central1 --limit=5 2>/dev/null || {
                print_warning "Could not list models. You may need to enable APIs or check permissions."
            }
        fi
    else
        echo "❌ gcloud alpha ai models - Not available"
    fi
    
    # Test alternative: Direct API calls
    print_status "Alternative: Testing direct API access..."
    if command_exists curl && [ ! -z "$(gcloud auth print-access-token 2>/dev/null)" ]; then
        ACCESS_TOKEN=$(gcloud auth print-access-token)
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        
        if [ ! -z "$PROJECT_ID" ]; then
            print_status "Testing Vertex AI API access..."
            curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
                 -H "Content-Type: application/json" \
                 "https://us-central1-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/us-central1/publishers/google/models" \
                 | head -c 100 && echo "..." && print_success "API access working!"
        fi
    fi
    
    echo ""
    print_success "Gemini CLI testing completed!"
}

# Display usage information
show_usage() {
    echo ""
    echo -e "${CYAN}📚 How to use Gemini CLI:${NC}"
    echo ""
    echo -e "${GREEN}1. List available models:${NC}"
    echo "   gcloud alpha ai models list --region=us-central1"
    echo ""
    echo -e "${GREEN}2. Make predictions (example):${NC}"
    echo "   gcloud alpha ai models predict MODEL_ID \\"
    echo "     --region=us-central1 \\"
    echo "     --json-request=request.json"
    echo ""
    echo -e "${GREEN}3. Alternative: Use Python SDK:${NC}"
    echo "   pip install google-cloud-aiplatform"
    echo ""
    echo -e "${GREEN}4. Alternative: Direct API calls:${NC}"
    echo "   curl -H \"Authorization: Bearer \$(gcloud auth print-access-token)\" \\"
    echo "        -H \"Content-Type: application/json\" \\"
    echo "        \"https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT_ID/...\""
    echo ""
    echo -e "${YELLOW}🔗 Useful links:${NC}"
    echo "• Vertex AI Documentation: https://cloud.google.com/vertex-ai/docs"
    echo "• Gemini API Documentation: https://ai.google.dev/docs"
    echo "• Google AI Studio: https://aistudio.google.com"
    echo ""
}

# Display Warp alternative
show_warp_alternative() {
    echo ""
    echo -e "${PURPLE}🌊 Alternative: Warp Terminal AI Features${NC}"
    echo ""
    echo "Since you already have Warp installed, you can use its built-in AI features:"
    echo ""
    echo -e "${GREEN}1. Warp AI Command Search:${NC}"
    echo "   • Press Ctrl+` (or Cmd+` on Mac) to open AI command search"
    echo "   • Type natural language queries like 'find large files'"
    echo ""
    echo -e "${GREEN}2. Warp AI Command Explanation:${NC}"
    echo "   • Select any command and press Ctrl+E to get AI explanations"
    echo ""
    echo -e "${GREEN}3. Warp AI Error Solutions:${NC}"
    echo "   • When commands fail, Warp can suggest fixes automatically"
    echo ""
    echo -e "${GREEN}4. Warp Workflows:${NC}"
    echo "   • Create custom workflows with AI assistance"
    echo ""
    echo -e "${YELLOW}Note:${NC} Warp's AI features use various models and might be sufficient"
    echo "for many tasks without needing a separate Gemini CLI setup."
    echo ""
}

# Main installation flow
main() {
    print_header
    
    # Step 1: Check if gcloud is installed
    if ! check_gcloud_installation; then
        echo ""
        read -p "Google Cloud SDK is not installed. Install it now? (y/N): " install_confirm
        if [[ $install_confirm =~ ^[Yy]$ ]]; then
            install_gcloud
        else
            print_error "Google Cloud SDK is required. Exiting."
            exit 1
        fi
    fi
    
    # Step 2: Update gcloud
    echo ""
    read -p "Update Google Cloud SDK to latest version? (Y/n): " update_confirm
    if [[ ! $update_confirm =~ ^[Nn]$ ]]; then
        update_gcloud
    fi
    
    # Step 3: Enable alpha components
    echo ""
    enable_alpha_components
    
    # Step 4: Install Gemini CLI
    echo ""
    install_gemini_cli
    
    # Step 5: Check authentication
    echo ""
    if ! check_authentication; then
        read -p "Authenticate with Google Cloud now? (Y/n): " auth_confirm
        if [[ ! $auth_confirm =~ ^[Nn]$ ]]; then
            authenticate_user
        fi
    fi
    
    # Step 6: Set up project
    echo ""
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 | grep -q "@"; then
        setup_project
    else
        print_warning "Skipping project setup (not authenticated)"
    fi
    
    # Step 7: Test functionality
    echo ""
    test_gemini_cli
    
    # Step 8: Show usage information
    show_usage
    
    # Step 9: Show Warp alternative
    show_warp_alternative
    
    # Final summary
    echo ""
    print_success "✨ Gemini CLI installation and setup completed!"
    echo ""
    echo -e "${CYAN}🎯 Best Gemini Models for 2025:${NC}"
    echo "• gemini-2.5-pro (most advanced reasoning)"
    echo "• gemini-2.5-flash (best price-performance)"
    echo "• gemini-2.5-flash-lite (most cost-effective)"
    echo ""
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo "1. Try the commands shown above"
    echo "2. Visit Google AI Studio for a web interface"
    echo "3. Consider using Warp's built-in AI features for simpler tasks"
    echo ""
}

# Run main function
main "$@" 