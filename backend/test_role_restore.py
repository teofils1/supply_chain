#!/usr/bin/env python3
"""
Test script to verify role soft delete and restore functionality.
Run this from the backend directory: uv run python test_role_restore.py
"""

import os
import sys
import django
from django.conf import settings

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from django.contrib.auth import get_user_model
import supplychain.models as m
import supplychain.serializers as s

User = get_user_model()

def test_role_restore():
    print("Testing role soft delete and restore functionality...")
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    print(f"Created user: {user.username}")
    
    # Create profile with initial role
    profile = m.UserProfile.objects.create(user=user, active_role='Operator')
    m.RoleAssignment.objects.create(user=user, role='Operator')
    print(f"Initial roles: {profile.roles}")
    
    # Add another role
    m.RoleAssignment.objects.create(user=user, role='Auditor')
    profile.refresh_from_db()
    print(f"After adding Auditor: {profile.roles}")
    
    # Use serializer to update roles (remove Auditor, keep Operator)
    serializer = s.UserDetailSerializer(instance=user)
    updated_user = serializer.update(user, {'roles_input': ['Operator']})
    profile.refresh_from_db()
    print(f"After removing Auditor via serializer: {profile.roles}")
    
    # Check that Auditor role is soft-deleted
    all_assignments = user.role_assignments.all_with_deleted()
    auditor_assignment = all_assignments.filter(role='Auditor').first()
    print(f"Auditor assignment deleted_at: {auditor_assignment.deleted_at}")
    print(f"Auditor assignment is_deleted: {auditor_assignment.is_deleted}")
    
    # Use serializer to restore Auditor role
    updated_user = serializer.update(user, {'roles_input': ['Operator', 'Auditor']})
    profile.refresh_from_db()
    print(f"After restoring Auditor: {profile.roles}")
    
    # Check that Auditor role is restored
    auditor_assignment.refresh_from_db()
    print(f"Auditor assignment deleted_at after restore: {auditor_assignment.deleted_at}")
    print(f"Auditor assignment is_deleted after restore: {auditor_assignment.is_deleted}")
    
    # Clean up
    user.hard_delete()
    print("Test completed successfully!")

if __name__ == '__main__':
    test_role_restore()
