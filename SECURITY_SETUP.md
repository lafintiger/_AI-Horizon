# 🔒 Security Setup Guide - AI-Horizon Project

**Last Updated**: June 28, 2025  
**Security Status**: ✅ **All API keys secured and rotated** - No sensitive data in version control

## ⚠️ CRITICAL: API Key Security

> **Recent Security Update (June 28, 2025)**: All exposed API keys have been rotated and secured. The repository is now safe for public access with proper `.gitignore` protection and environment variable management.

### **Environment Variables Setup**

1. **Copy the template:**
   ```bash
   cp env.template config.env
   ```

2. **Add your API keys to `config.env`:**
   - Replace `your_perplexity_api_key_here` with your actual Perplexity API key
   - Replace `your_openai_api_key_here` with your actual OpenAI API key  
   - Replace `your_anthropic_api_key_here` with your actual Anthropic API key

3. **NEVER commit `config.env` to git** - it's already in `.gitignore`

### **Heroku Environment Variables**

Set environment variables in Heroku (not in files):

```bash
heroku config:set PERPLEXITY_API_KEY=your_actual_key --app ai-horizon-portal
heroku config:set OPENAI_API_KEY=your_actual_key --app ai-horizon-portal  
heroku config:set ANTHROPIC_API_KEY=your_actual_key --app ai-horizon-portal
```

### **Local Development**

For local development, the app will load from `config.env` automatically.

### **🚨 Security Best Practices**

1. **Never commit API keys to version control**
2. **Rotate keys immediately if exposed**
3. **Use different keys for development/production**
4. **Monitor API usage for unauthorized access**
5. **Keep `.gitignore` updated to exclude sensitive files**

### **If API Keys Are Compromised:**

1. **Immediately revoke/rotate** the exposed keys in each service:
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/
   - Perplexity: https://www.perplexity.ai/settings/api

2. **Update your local `config.env` with new keys**
3. **Update Heroku environment variables with new keys**
4. **Monitor accounts for unauthorized usage**

## 🔍 Checking Current Setup

To verify your environment is properly configured:

```bash
# Check local config (should show keys are loaded)
python -c "from aih.config import get_api_key; print('✅ Keys loaded' if get_api_key('openai') else '❌ Keys missing')"

# Check Heroku config  
heroku config --app ai-horizon-portal
``` 