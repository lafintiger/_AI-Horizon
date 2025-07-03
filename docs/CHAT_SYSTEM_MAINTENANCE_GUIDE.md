# Chat System Maintenance Guide

## 🎯 Purpose
This guide prevents regressions and maintains the reliability of the AI-Horizon chat system based on lessons learned from production issues.

## 🚨 Critical Issues to Prevent

### 1. Library Version Incompatibility

**Issue**: `Client.__init__() got an unexpected keyword argument 'proxies'`

**Root Cause**: Using outdated `anthropic` library (≤0.37.x) with modern deployment environments.

**Prevention**:
- ✅ **Always use `anthropic>=0.40.0`** in requirements.txt
- ✅ **Pin minimum versions** for critical libraries
- ✅ **Test library compatibility** before deployment

```bash
# Check current versions
pip list | grep -E "(anthropic|openai|flask)"

# Upgrade if needed
pip install anthropic>=0.40.0 openai>=1.0.0
```

### 2. API Key Authentication Failures

**Issue**: `Error code: 401 - authentication_error: invalid x-api-key`

**Root Cause**: Missing or incorrectly formatted API keys in environment.

**Prevention**:
- ✅ **Set API keys before starting server**:
  ```bash
  export ANTHROPIC_API_KEY="sk-ant-api03-..."
  export OPENAI_API_KEY="sk-proj-..."
  ```
- ✅ **Verify key format** (minimum 20 characters)
- ✅ **Test API connectivity** before deployment

### 3. Missing Flask Routes

**Issue**: `BuildError: Could not build url for endpoint 'chat'`

**Root Cause**: Template references undefined Flask routes.

**Prevention**:
- ✅ **Verify all routes are registered** in `status_server.py`
- ✅ **Check template references** match actual endpoints
- ✅ **Test route accessibility** after code changes

### 4. Template and Static File Issues

**Issue**: `TemplateNotFound: base.html` or missing static assets

**Root Cause**: Missing or moved template files.

**Prevention**:
- ✅ **Keep templates in `/templates/` directory**
- ✅ **Maintain template inheritance chain** (base.html → specific templates)
- ✅ **Verify static file paths** after restructuring

## 🛡️ Automated Prevention System

### Health Monitor Usage

Run the health monitor **before every deployment**:

```bash
# Basic health check
python scripts/system_health_monitor.py

# Check running server too
python scripts/system_health_monitor.py --check-server

# Check specific port
python scripts/system_health_monitor.py --check-server --port 8000
```

### Deployment Checklist

**Before starting the server:**

1. **Run Health Check**:
   ```bash
   python scripts/system_health_monitor.py
   ```

2. **Verify API Keys**:
   ```bash
   echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:10}..."
   echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}..."
   ```

3. **Check Library Versions**:
   ```bash
   pip show anthropic openai | grep Version
   ```

4. **Test Database Connection**:
   ```bash
   python -c "from aih.utils.database import DatabaseManager; print(DatabaseManager().get_database_stats())"
   ```

5. **Verify Flask Routes**:
   ```bash
   python -c "import status_server; print(f'Chat route: {[\"/chat\" in str(rule) for rule in status_server.app.url_map.iter_rules()]}')"
   ```

## 🔧 Troubleshooting Common Issues

### Chat Returns "❌ Error generating response"

**Diagnosis Steps**:
1. Check server logs for specific error
2. Verify API key is set and valid
3. Test API connectivity manually
4. Check library versions

**Quick Fix**:
```bash
# Test API directly
python -c "
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model='claude-3-5-sonnet-20241022',
    max_tokens=10,
    messages=[{'role': 'user', 'content': 'test'}]
)
print('API working:', response.content[0].text)
"
```

### Chat Interface Not Loading

**Diagnosis Steps**:
1. Check if `/chat` route is registered
2. Verify template files exist
3. Check browser console for JS errors
4. Verify authentication/permissions

**Quick Fix**:
```bash
# Check route registration
python -c "
import status_server
routes = [str(rule) for rule in status_server.app.url_map.iter_rules()]
print('Chat route exists:', '/chat' in routes)
"
```

### Library Import Errors

**Diagnosis Steps**:
1. Check Python path
2. Verify virtual environment
3. Reinstall problematic packages
4. Check for version conflicts

**Quick Fix**:
```bash
# Reinstall core packages
pip install --force-reinstall anthropic openai flask
```

## 📊 Monitoring and Alerts

### Continuous Monitoring

**Set up periodic health checks**:

```bash
# Add to cron (every hour)
0 * * * * cd /path/to/ai-horizon && python scripts/system_health_monitor.py >> logs/health_check.log 2>&1
```

### Performance Monitoring

**Key metrics to watch**:
- Chat response time (should be <30 seconds)
- API error rates (should be <5%)
- Database connection time (should be <1 second)
- Memory usage trends

### Alert Thresholds

**Set up alerts for**:
- Health check failures
- API authentication errors
- High chat response times
- Library version mismatches

## 🚀 Best Practices

### Development

1. **Always test chat locally** before deployment
2. **Use health monitor** in CI/CD pipeline
3. **Keep API keys in environment**, not code
4. **Pin minimum library versions** in requirements.txt
5. **Test with actual API calls**, not just imports

### Deployment

1. **Run health check first**: `python scripts/system_health_monitor.py`
2. **Set environment variables** before starting server
3. **Test critical endpoints** after deployment
4. **Monitor logs** for first few minutes
5. **Have rollback plan** ready

### Maintenance

1. **Update libraries quarterly** with testing
2. **Rotate API keys annually** or as needed
3. **Monitor API usage** and costs
4. **Review logs weekly** for patterns
5. **Update documentation** when making changes

## 📋 Emergency Recovery

### Chat System Completely Down

**Immediate Steps**:
1. Check server status: `curl http://localhost:8000/api/database_stats`
2. Run health monitor: `python scripts/system_health_monitor.py`
3. Check logs: `tail -50 logs/system.log`
4. Verify API keys: Test with simple API call
5. Restart with clean environment

**Recovery Commands**:
```bash
# Stop server
pkill -f status_server.py

# Set API keys
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"

# Update libraries if needed
pip install anthropic>=0.40.0

# Run health check
python scripts/system_health_monitor.py

# Start server
python status_server.py --host 0.0.0.0 --port 8000
```

### API Authentication Errors

**Quick Recovery**:
```bash
# Test current keys
echo "Testing API keys..."
python -c "
import os
import anthropic
if os.getenv('ANTHROPIC_API_KEY'):
    client = anthropic.Anthropic()
    try:
        response = client.messages.create(
            model='claude-3-5-sonnet-20241022',
            max_tokens=5,
            messages=[{'role': 'user', 'content': 'test'}]
        )
        print('✅ Anthropic API working')
    except Exception as e:
        print(f'❌ Anthropic API error: {e}')
else:
    print('❌ ANTHROPIC_API_KEY not set')
"
```

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-06-30 | Initial guide after chat system fixes |
| 1.1 | 2025-06-30 | Added health monitor integration |

## 📞 Support

For issues not covered in this guide:
1. Check the health monitor output
2. Review system logs
3. Test individual components
4. Refer to the main documentation
5. Create detailed issue report with logs

---

**Remember**: The chat system is critical for user interaction. Prevention is always better than recovery! 