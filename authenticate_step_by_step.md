# 🔐 Google Cloud Authentication for WSL

## Quick Authentication Steps

### Option 1: Direct Command (Recommended)

1. **Open a new terminal** and run:
```bash
gcloud auth login --no-browser
```

2. **Copy the URL** that appears and paste it into your web browser

3. **Complete authentication** in your browser:
   - Log in with your Google account
   - Accept the permissions
   - Copy the verification code that appears

4. **Paste the verification code** back into your terminal

### Option 2: Application Default Credentials

1. **Run this command**:
```bash
gcloud auth application-default login --no-browser
```

2. **Copy the URL** to your browser

3. **After browser authentication**, you'll see a command like:
```bash
gcloud auth application-default login --remote-bootstrap="..."
```

4. **Copy and run** that entire command in your terminal

### Option 3: Check if Already Authenticated

Run this to check current status:
```bash
gcloud auth list
```

If you see an active account with an email address, you're already authenticated!

## Set Up Project (After Authentication)

1. **List available projects**:
```bash
gcloud projects list
```

2. **Set your project** (replace with your project ID):
```bash
gcloud config set project YOUR_PROJECT_ID
```

3. **Enable required APIs**:
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable ml.googleapis.com
```

## Test Authentication

Run this to verify everything works:
```bash
gcloud auth list
gcloud config get-value project
```

You should see:
- ✅ An active account 
- ✅ A configured project

## Troubleshooting

If you get "Operation not supported" errors:
- Make sure you're using `--no-browser` flag
- Copy URLs manually to your browser
- Don't expect automatic browser opening in WSL

## Next Steps

After authentication is complete:
1. Go to http://localhost:8501
2. Click the "🤖 Gemini CLI" tab  
3. The system should now show "✅ Authenticated" 