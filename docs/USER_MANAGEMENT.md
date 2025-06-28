# User Management System

## Overview

The AI-Horizon system includes a comprehensive user management system that allows administrators to control access and manage user accounts. The system supports role-based access control with three distinct user roles.

## User Roles

### Administrator (admin)
- **Full system access** with all permissions
- Can manage other users (add, delete, reset passwords)
- Can access all features including analysis tools, collection management, and settings
- Can export data and reports
- Can reprocess data and manage system operations

### Viewer (viewer)
- **Read-only access** to view data and reports
- Can browse entries and view analysis results
- Can export data and reports
- Cannot modify data or run analysis operations
- Cannot access user management or system settings

### Manual Entry (manual_entry)
- Can **add documents manually** through the manual entry interface
- Can view existing data and reports
- Can export data and reports
- Cannot run analysis operations or modify system settings
- Cannot manage users

## User Management Interface

### Accessing User Management
1. Log in as an administrator
2. Navigate to **Settings → User Management** in the main navigation
3. The user management page will display all existing users and management options

### Adding New Users
1. In the "Add New User" section, fill out:
   - **Username**: Minimum 3 characters, must be unique
   - **Full Name**: Display name for the user
   - **Role**: Select from Administrator, Viewer, or Manual Entry
   - **Password**: Minimum 6 characters
   - **Confirm Password**: Must match the password
2. Click "Create User"
3. The new user will appear in the users table

### Changing Your Password
1. In the "Change Your Password" section:
   - Enter your current password
   - Enter your new password (minimum 6 characters)
   - Confirm your new password
2. Click "Change Password"

### Managing Existing Users

#### Resetting Another User's Password (Admin Only)
1. In the users table, click "Reset Password" next to any user
2. Enter the new password when prompted (minimum 6 characters)
3. The user will need to use the new password on their next login

#### Deleting Users (Admin Only)
1. In the users table, click "Delete" next to any user
2. Confirm the deletion when prompted
3. **Note**: The admin user cannot be deleted for security reasons

## Default Users

The system comes with three default users:

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| admin | admin123 | Administrator | Full system access |
| viewer | viewer123 | Viewer | Read-only access |
| manual | manual123 | Manual Entry | Can add documents |

**⚠️ Security Warning**: Change these default passwords immediately after installation!

## User Data Storage

- User data is stored in `data/users.json`
- Passwords are hashed using SHA-256 for security
- User sessions expire after 8 hours of inactivity
- The system automatically creates the users file on first run

## API Endpoints

The user management system provides several API endpoints for programmatic access:

### POST /api/add_user
Add a new user (admin only)
```json
{
  "username": "newuser",
  "name": "New User",
  "role": "viewer",
  "password": "securepassword"
}
```

### POST /api/change_password
Change current user's password
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword"
}
```

### POST /api/reset_password
Reset another user's password (admin only)
```json
{
  "username": "targetuser",
  "new_password": "newpassword"
}
```

### POST /api/delete_user
Delete a user (admin only)
```json
{
  "username": "usertodellete"
}
```

### GET /api/list_users
Get list of all users (admin only)

## Security Features

1. **Password Requirements**: Minimum 6 characters
2. **Password Hashing**: SHA-256 encryption for stored passwords
3. **Session Management**: 8-hour session timeout
4. **Role-Based Access**: Strict permission checking for all operations
5. **Admin Protection**: Admin user cannot be deleted
6. **Self-Protection**: Users cannot delete their own accounts
7. **Input Validation**: All user inputs are validated and sanitized

## Troubleshooting

### Cannot Access User Management
- Ensure you're logged in as an administrator
- Only admin users can see the "User Management" link in the navigation

### Password Reset Not Working
- Verify the new password meets minimum requirements (6 characters)
- Check that you have admin privileges for resetting other users' passwords

### User Creation Fails
- Check that the username is unique and at least 3 characters
- Ensure the password meets minimum requirements
- Verify you have admin privileges

### Lost Admin Access
If you lose admin access:
1. Stop the server
2. Delete the `data/users.json` file
3. Restart the server (this will recreate default users)
4. Log in with admin/admin123 and change the password immediately

## Best Practices

1. **Change Default Passwords**: Immediately change all default passwords after installation
2. **Use Strong Passwords**: Require users to use passwords longer than the minimum 6 characters
3. **Regular Password Updates**: Encourage users to change passwords regularly
4. **Principle of Least Privilege**: Assign users the minimum role necessary for their tasks
5. **Monitor User Activity**: Review user login times and activity regularly
6. **Backup User Data**: Include `data/users.json` in your backup procedures

## Future Enhancements

Planned improvements to the user management system:
- Password complexity requirements
- Multi-factor authentication
- User activity logging
- Password expiration policies
- Integration with external authentication systems (LDAP, OAuth)
- Bulk user import/export functionality 