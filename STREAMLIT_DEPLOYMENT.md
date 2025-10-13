# Manga Lookup Tool - Streamlit Deployment Guide

## 🚀 Overview

This document provides instructions for deploying the Manga Lookup Tool as a Streamlit web application.

## 📋 Prerequisites

- Python 3.8+
- Streamlit Cloud account (free)
- DeepSeek API key

## 🛠️ Development Workflow

### Option 1: Test Core Logic (Recommended for Termux)

Since Streamlit may not install on Termux due to libc compatibility, you can test the core logic:

```bash
# Test core functionality
python test_core_logic.py

# Test with your API key
export DEEPSEEK_API_KEY="your_api_key_here"
python test_core_logic.py
```

### Option 2: Local Streamlit Development (if available)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
# Create .streamlit/secrets.toml with your API key

# Run locally
streamlit run streamlit_app.py
```

### Option 3: Direct Deployment to Streamlit Cloud

Skip local testing and deploy directly to Streamlit Cloud.

## ☁️ Streamlit Cloud Deployment

### 1. Prepare Repository

- Ensure all files are committed to GitHub
- Verify `requirements.txt` includes all dependencies
- Create `.streamlit/secrets.toml` in your repository

### 2. Deploy to Streamlit Cloud

1. Go to [Streamlit Cloud](https://share.streamlit.io/)
2. Connect your GitHub repository
3. Set the main file path to `streamlit_app.py`
4. Add your DeepSeek API key as a secret in the Streamlit Cloud dashboard

### 3. Configure Secrets

In Streamlit Cloud dashboard:
- Go to your app settings
- Click "Secrets"
- Add:

```toml
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
```

## 📁 File Structure

```
├── streamlit_app.py          # Main Streamlit application
├── manga_lookup.py           # Core logic (unchanged)
├── marc_exporter.py          # MARC export functionality
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── secrets.toml         # API keys (local only)
└── STREAMLIT_DEPLOYMENT.md  # This file
```

## 🎨 Features

### User Interface
- **Multi-series input**: Add multiple manga series with volume ranges
- **Progress tracking**: Real-time progress counter with ETA
- **Animated duck**: CSS-animated duck drinking coffee during processing
- **Expandable results**: Collapsible table showing all books
- **Modal details**: Clickable rows show full book information
- **Export options**: Download JSON and MARC files

### Core Functionality
- **Volume range parsing**: Supports traditional ranges (1-5) and omnibus formats (17-18-19)
- **Series name correction**: AI-powered series name suggestions
- **Barcode assignment**: Sequential barcode generation
- **MARC export**: Library-compatible MARC21 records
- **Caching**: Automatic caching of API responses

## 🔧 Configuration

### API Key Setup

The app requires a DeepSeek API key. This can be provided via:

1. **Streamlit Secrets** (recommended for deployment)
2. **Environment variables** (for local development)
3. **User input** (not implemented yet)

### Rate Limiting

The app implements 1-second rate limiting between API calls to comply with DeepSeek's usage policies.

## 🐛 Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure all dependencies in `requirements.txt` are installed
2. **API Key Error**: Verify your DeepSeek API key is correctly set in secrets
3. **Import Errors**: Check that `manga_lookup.py` and `marc_exporter.py` are in the same directory

### Performance Tips

- Use cached data when available to reduce API calls
- Process smaller batches for faster results
- Monitor API usage through DeepSeek dashboard

## 📞 Support

For issues with:
- **Streamlit deployment**: Check Streamlit Cloud documentation
- **API integration**: Refer to DeepSeek API documentation
- **Application logic**: Review the original CLI tool documentation

## 🔄 Updates

To update the deployed app:
1. Push changes to GitHub
2. Streamlit Cloud automatically redeploys
3. Monitor deployment status in the Streamlit Cloud dashboard

---

**Note**: This app makes external API calls to DeepSeek. Ensure you comply with their terms of service and monitor your API usage.