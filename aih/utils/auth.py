"""
Authentication and authorization utilities for AI-Horizon system.
"""

from functools import wraps
from flask import session, request, redirect, url_for, jsonify
from typing import Dict, List, Optional
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

# User roles and their permissions
USER_ROLES = {
    'admin': {
        'name': 'Administrator',
        'permissions': [
            'view_all', 'edit_all', 'delete_all', 'manage_users',
            'run_analysis', 'export_data', 'manual_entry', 'view_reports',
            'access_settings', 'manage_collection', 'reprocess_data'
        ],
        'description': 'Full system access with all permissions'
    },
    'viewer': {
        'name': 'Viewer',
        'permissions': [
            'view_all', 'view_reports', 'export_data'
        ],
        'description': 'Read-only access to view data and reports'
    },
    'manual_entry': {
        'name': 'Manual Entry',
        'permissions': [
            'view_all', 'manual_entry', 'view_reports', 'export_data'
        ],
        'description': 'Can add documents manually and view existing data'
    }
}

# Default users (in production, these should be in a secure database)
DEFAULT_USERS = {
    'admin': {
        'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
        'role': 'admin',
        'name': 'System Administrator',
        'created_at': '2025-06-28T00:00:00',
        'last_login': None
    },
    'viewer': {
        'password_hash': hashlib.sha256('viewer123'.encode()).hexdigest(),
        'role': 'viewer',
        'name': 'System Viewer',
        'created_at': '2025-06-28T00:00:00',
        'last_login': None
    },
    'manual': {
        'password_hash': hashlib.sha256('manual123'.encode()).hexdigest(),
        'role': 'manual_entry',
        'name': 'Manual Entry User',
        'created_at': '2025-06-28T00:00:00',
        'last_login': None
    }
}

class AuthManager:
    def __init__(self, users_file='data/users.json'):
        self.users_file = users_file
        self.session_key = 'ai_horizon_user'
        self.users = self._load_users()
        
        # Rate limiting for authentication attempts
        self.failed_attempts = defaultdict(list)
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    def _load_users(self) -> Dict:
        """Load users from file or create default users."""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default users and save them
                self._save_users(DEFAULT_USERS)
                return DEFAULT_USERS.copy()
        except Exception as e:
            print(f"Error loading users: {e}")
            return DEFAULT_USERS.copy()
    
    def _save_users(self, users_data: Dict = None) -> bool:
        """Save users to file."""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            
            users_to_save = users_data if users_data is not None else self.users
            with open(self.users_file, 'w') as f:
                json.dump(users_to_save, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving users: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user credentials with rate limiting."""
        if username not in self.users:
            return None
        
        # Check for rate limiting
        now = datetime.now()
        if self.is_user_locked_out(username):
            return None
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user_data = self.users[username]
        
        if user_data['password_hash'] == password_hash:
            # Successful login - clear failed attempts
            if username in self.failed_attempts:
                del self.failed_attempts[username]
            
            # Update last login
            self.users[username]['last_login'] = datetime.now().isoformat()
            self._save_users()
            
            return {
                'username': username,
                'role': user_data['role'],
                'name': user_data['name'],
                'permissions': USER_ROLES[user_data['role']]['permissions']
            }
        else:
            # Failed login - record attempt
            self.failed_attempts[username].append(now)
            return None
    
    def is_user_locked_out(self, username: str) -> bool:
        """Check if user is locked out due to failed login attempts."""
        if username not in self.failed_attempts:
            return False
        
        now = datetime.now()
        # Remove old attempts outside lockout duration
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username]
            if now - attempt < self.lockout_duration
        ]
        
        # Check if user has exceeded max attempts
        return len(self.failed_attempts[username]) >= self.max_attempts
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user from session."""
        if self.session_key in session:
            username = session[self.session_key]
            if username in self.users:
                user_data = self.users[username]
                return {
                    'username': username,
                    'role': user_data['role'],
                    'name': user_data['name'],
                    'permissions': USER_ROLES[user_data['role']]['permissions']
                }
        return None
    
    def login_user(self, username: str) -> None:
        """Log in user by setting session."""
        session[self.session_key] = username
        session.permanent = True
    
    def logout_user(self) -> None:
        """Log out user by clearing session."""
        session.pop(self.session_key, None)
    
    def is_authenticated(self) -> bool:
        """Check if current user is authenticated."""
        return self.get_current_user() is not None
    
    def has_permission(self, permission: str) -> bool:
        """Check if current user has specific permission."""
        user = self.get_current_user()
        if not user:
            return False
        return permission in user['permissions']
    
    def get_role_info(self, role: str) -> Optional[Dict]:
        """Get information about a specific role."""
        return USER_ROLES.get(role)
    
    def add_user(self, username: str, password: str, role: str, name: str) -> Dict:
        """Add a new user."""
        if username in self.users:
            return {'success': False, 'error': 'Username already exists'}
        
        if role not in USER_ROLES:
            return {'success': False, 'error': 'Invalid role'}
        
        if len(username) < 3:
            return {'success': False, 'error': 'Username must be at least 3 characters'}
        
        if len(password) < 8:
            return {'success': False, 'error': 'Password must be at least 8 characters'}
        
        # Enhanced password validation
        if not any(c.isupper() for c in password):
            return {'success': False, 'error': 'Password must contain at least one uppercase letter'}
        if not any(c.islower() for c in password):
            return {'success': False, 'error': 'Password must contain at least one lowercase letter'}
        if not any(c.isdigit() for c in password):
            return {'success': False, 'error': 'Password must contain at least one number'}
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return {'success': False, 'error': 'Password must contain at least one special character'}
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        self.users[username] = {
            'password_hash': password_hash,
            'role': role,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        if self._save_users():
            return {'success': True, 'message': f'User {username} created successfully'}
        else:
            # Rollback
            del self.users[username]
            return {'success': False, 'error': 'Failed to save user data'}
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Dict:
        """Change user password."""
        if username not in self.users:
            return {'success': False, 'error': 'User not found'}
        
        if len(new_password) < 8:
            return {'success': False, 'error': 'New password must be at least 8 characters'}
        
        # Enhanced password validation
        if not any(c.isupper() for c in new_password):
            return {'success': False, 'error': 'New password must contain at least one uppercase letter'}
        if not any(c.islower() for c in new_password):
            return {'success': False, 'error': 'New password must contain at least one lowercase letter'}
        if not any(c.isdigit() for c in new_password):
            return {'success': False, 'error': 'New password must contain at least one number'}
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in new_password):
            return {'success': False, 'error': 'New password must contain at least one special character'}
        
        # Verify old password
        old_password_hash = hashlib.sha256(old_password.encode()).hexdigest()
        if self.users[username]['password_hash'] != old_password_hash:
            return {'success': False, 'error': 'Current password is incorrect'}
        
        # Set new password
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        self.users[username]['password_hash'] = new_password_hash
        
        if self._save_users():
            return {'success': True, 'message': 'Password changed successfully'}
        else:
            # Rollback
            self.users[username]['password_hash'] = old_password_hash
            return {'success': False, 'error': 'Failed to save password change'}
    
    def reset_password(self, username: str, new_password: str) -> Dict:
        """Reset user password (admin only)."""
        if username not in self.users:
            return {'success': False, 'error': 'User not found'}
        
        if len(new_password) < 8:
            return {'success': False, 'error': 'New password must be at least 8 characters'}
        
        # Enhanced password validation
        if not any(c.isupper() for c in new_password):
            return {'success': False, 'error': 'New password must contain at least one uppercase letter'}
        if not any(c.islower() for c in new_password):
            return {'success': False, 'error': 'New password must contain at least one lowercase letter'}
        if not any(c.isdigit() for c in new_password):
            return {'success': False, 'error': 'New password must contain at least one number'}
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in new_password):
            return {'success': False, 'error': 'New password must contain at least one special character'}
        
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        old_hash = self.users[username]['password_hash']
        self.users[username]['password_hash'] = new_password_hash
        
        if self._save_users():
            return {'success': True, 'message': f'Password reset for user {username}'}
        else:
            # Rollback
            self.users[username]['password_hash'] = old_hash
            return {'success': False, 'error': 'Failed to save password reset'}
    
    def update_user(self, username: str, name: str = None, role: str = None) -> Dict:
        """Update user information."""
        if username not in self.users:
            return {'success': False, 'error': 'User not found'}
        
        if role and role not in USER_ROLES:
            return {'success': False, 'error': 'Invalid role'}
        
        old_data = self.users[username].copy()
        
        if name:
            self.users[username]['name'] = name
        if role:
            self.users[username]['role'] = role
        
        if self._save_users():
            return {'success': True, 'message': f'User {username} updated successfully'}
        else:
            # Rollback
            self.users[username] = old_data
            return {'success': False, 'error': 'Failed to save user update'}
    
    def delete_user(self, username: str) -> Dict:
        """Delete a user."""
        if username not in self.users:
            return {'success': False, 'error': 'User not found'}
        
        if username == 'admin':
            return {'success': False, 'error': 'Cannot delete admin user'}
        
        user_data = self.users[username]
        del self.users[username]
        
        if self._save_users():
            return {'success': True, 'message': f'User {username} deleted successfully'}
        else:
            # Rollback
            self.users[username] = user_data
            return {'success': False, 'error': 'Failed to delete user'}
    
    def list_users(self) -> List[Dict]:
        """Get list of all users (without password hashes)."""
        users_list = []
        for username, user_data in self.users.items():
            users_list.append({
                'username': username,
                'name': user_data['name'],
                'role': user_data['role'],
                'role_name': USER_ROLES[user_data['role']]['name'],
                'created_at': user_data.get('created_at', 'Unknown'),
                'last_login': user_data.get('last_login', 'Never')
            })
        return sorted(users_list, key=lambda x: x['username'])

# Global auth manager instance
auth_manager = AuthManager()

def login_required(f):
    """Decorator to require authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth_manager.is_authenticated():
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission: str):
    """Decorator to require specific permission for routes."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not auth_manager.is_authenticated():
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login'))
            
            if not auth_manager.has_permission(permission):
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                return redirect(url_for('access_denied'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role for routes."""
    return permission_required('manage_users')(f)

def get_user_context():
    """Get user context for templates."""
    user = auth_manager.get_current_user()
    if user:
        role_info = auth_manager.get_role_info(user['role'])
        return {
            'user': user,
            'role_info': role_info,
            'is_authenticated': True
        }
    return {
        'user': None,
        'role_info': None,
        'is_authenticated': False
    } 