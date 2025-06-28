# AI-Horizon Authentication System

## Overview

The AI-Horizon system now includes a comprehensive role-based authentication system that controls access to different features based on user roles and permissions.

## User Roles

### 🔧 Administrator
- **Username**: `admin`
- **Password**: `admin123`
- **Permissions**: Full system access
  - View all data and reports
  - Run analysis and predictions
  - Manage collections and reprocessing
  - Access settings and system management
  - Manual entry capabilities
  - Export data and reports
  - User management (future)

### 👁️ Viewer
- **Username**: `viewer`
- **Password**: `viewer123`
- **Permissions**: Read-only access
  - View all data and reports
  - Export data and reports
  - Browse entries and view content
  - **Cannot**: Add/edit data, run analysis, access settings

### 📝 Manual Entry
- **Username**: `manual`
- **Password**: `manual123`
- **Permissions**: Data entry and viewing
  - View all data and reports
  - Manual entry capabilities (add URLs, files, YouTube videos)
  - Export data and reports
  - **Cannot**: Run analysis, access settings, manage collections

## Authentication Features

### Session Management
- 8-hour session timeout
- Secure session cookies
- Automatic logout on session expiration
- Remember originally requested page after login

### Access Control
- Route-level permission checking
- Automatic redirection to login for unauthenticated users
- Access denied page for insufficient permissions
- Role-based UI element visibility

### Security Features
- Password hashing (SHA-256)
- Session-based authentication
- CSRF protection via Flask's built-in mechanisms
- Secure cookie configuration

## Protected Routes

### Admin Only
- `/settings` - System configuration
- Collection management APIs
- User management (future)

### Manual Entry Permission Required
- `/manual_entry` - Manual entry dashboard
- `/add_url` - Add URL form
- `/add_file` - Add file form
- `/add_youtube` - Add YouTube video form

### Analysis Permission Required
- `/analysis` - Analysis dashboard
- `/predictive_analytics` - ML predictions
- Analysis API endpoints

### View Permission Required
- `/` - Main dashboard
- `/browse_entries` - Browse all entries
- `/chat` - RAG chat interface
- `/methodology` - Documentation
- Most viewing endpoints

### Reports Permission Required
- `/reports` - Intelligence reports
- `/summaries` - Category summaries
- Report generation APIs

## Login Process

1. **Access Protected Route**: User tries to access any protected route
2. **Authentication Check**: System checks for valid session
3. **Redirect to Login**: If not authenticated, redirect to `/login`
4. **Credential Validation**: User enters username/password
5. **Permission Assignment**: System assigns role-based permissions
6. **Session Creation**: Valid login creates secure session
7. **Redirect to Destination**: User redirected to originally requested page

## Access Denied Flow

1. **Permission Check**: System validates user permissions for route
2. **Access Denied**: If insufficient permissions, redirect to `/access_denied`
3. **User Information**: Access denied page shows current user info and role
4. **Navigation Options**: User can go back, return home, or logout

## Implementation Details

### Authentication Module (`aih/utils/auth.py`)
- `AuthManager` class handles all authentication logic
- Role and permission definitions
- Session management utilities
- Decorator functions for route protection

### Route Decorators
- `@login_required` - Requires valid authentication
- `@permission_required('permission')` - Requires specific permission
- `@admin_required` - Requires admin role

### Template Integration
- User context automatically injected into all templates
- Role-based UI element visibility
- User information display in navigation

## Quick Login Shortcuts (Development)

For development convenience, the login page supports keyboard shortcuts:
- `Ctrl+Shift+A` - Auto-fill admin credentials
- `Ctrl+Shift+V` - Auto-fill viewer credentials  
- `Ctrl+Shift+M` - Auto-fill manual entry credentials

## Testing Authentication

### Command Line Testing
```bash
# Test unauthenticated access (should redirect)
curl -I http://127.0.0.1:8000/

# Test login
curl -c cookies.txt -d "username=admin&password=admin123" -X POST http://127.0.0.1:8000/login

# Test authenticated access
curl -b cookies.txt http://127.0.0.1:8000/

# Test access control
curl -b cookies.txt http://127.0.0.1:8000/manual_entry
```

### Browser Testing
1. Navigate to `http://127.0.0.1:8000/`
2. Should automatically redirect to login page
3. Try different user credentials
4. Verify access to appropriate features based on role
5. Test logout functionality

## Security Considerations

### Current Implementation
- Basic password hashing (suitable for development/demo)
- Session-based authentication
- Role-based access control
- Secure cookie configuration

### Production Recommendations
- Implement stronger password hashing (bcrypt, scrypt, or Argon2)
- Add password complexity requirements
- Implement account lockout after failed attempts
- Add two-factor authentication
- Use environment variables for secrets
- Implement proper user management interface
- Add audit logging for authentication events
- Consider JWT tokens for API access

## Future Enhancements

1. **User Management Interface**
   - Admin panel for user creation/management
   - Password reset functionality
   - Role assignment interface

2. **Enhanced Security**
   - Two-factor authentication
   - Password complexity requirements
   - Account lockout protection
   - Audit logging

3. **API Authentication**
   - JWT token support
   - API key management
   - Rate limiting per user

4. **Integration Features**
   - LDAP/Active Directory integration
   - Single Sign-On (SSO) support
   - OAuth2 provider integration

## Troubleshooting

### Common Issues

**Login Page Not Found (404)**
- Check that authentication routes are properly imported
- Verify Flask app configuration
- Ensure `aih/utils/auth.py` is accessible

**Permission Denied for Valid User**
- Check user role assignments in `DEFAULT_USERS`
- Verify permission definitions in `USER_ROLES`
- Check route decorator configuration

**Session Not Persisting**
- Verify Flask secret key is set
- Check session timeout configuration
- Ensure cookies are enabled in browser

**Access Denied Page Not Showing User Info**
- Check template context injection
- Verify `get_user_context()` function
- Ensure session data is valid

### Debug Mode
Enable Flask debug mode to see detailed error messages:
```bash
python status_server.py --port 8000 --debug
```

## File Structure

```
aih/utils/auth.py              # Authentication module
templates/login.html           # Login page template
templates/access_denied.html   # Access denied page template
status_server.py              # Main server with auth integration
docs/AUTHENTICATION_SYSTEM.md # This documentation
```

The authentication system provides a solid foundation for controlling access to the AI-Horizon intelligence platform while maintaining usability and security best practices. 