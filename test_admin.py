import unittest
from app import app, db, User, File, AccessLog, FileVersion, FileTag
from datetime import datetime
import os

class TestAdminFunctions(unittest.TestCase):
    def setUp(self):
        # Configure test database
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database
        app.config['UPLOAD_FOLDER'] = 'test_uploads'
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
        
        # Create unique Ethereum addresses using timestamp
        timestamp = int(datetime.utcnow().timestamp())
        admin_eth = f'0x123456789012345678901234567890123456{timestamp}'
        user_eth = f'0x987654321098765432109876543210987654{timestamp}'
        
        # Create test admin user
        self.admin = User(
            username='testadmin',
            email='testadmin@example.com',
            role='admin',
            department='management',
            ethereum_address=admin_eth
        )
        self.admin.set_password('test123')
        db.session.add(self.admin)
        db.session.commit()
        
        # Create test regular user
        self.user = User(
            username='testuser',
            email='testuser@example.com',
            role='user',
            department='finance',
            ethereum_address=user_eth
        )
        self.user.set_password('test123')
        db.session.add(self.user)
        db.session.commit()
        
        # Create test file
        self.file = File(
            filename='test.txt',
            file_hash='testhash',
            file_type='text/plain',
            department='finance',
            user_id=self.user.id,
            file_size=1024,
            file_path='test.txt'
        )
        db.session.add(self.file)
        db.session.commit()
        
        # Create test uploads directory
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Create a test file in the uploads directory
        with open(os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt'), 'w') as f:
            f.write('test content')

    def tearDown(self):
        # Clean up test files
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt')):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt'))
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            os.rmdir(app.config['UPLOAD_FOLDER'])
        
        # Clean up database
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login_admin(self):
        # Use the test client to login
        response = self.client.post('/login', data={
            'username': 'testadmin',
            'password': 'test123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard(self):
        self.login_admin()
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)

    def test_admin_files(self):
        self.login_admin()
        response = self.client.get('/admin/files')
        self.assertEqual(response.status_code, 200)

    def test_admin_users(self):
        self.login_admin()
        response = self.client.get('/admin/users')
        self.assertEqual(response.status_code, 200)

    def test_admin_activity(self):
        self.login_admin()
        response = self.client.get('/admin/activity')
        self.assertEqual(response.status_code, 200)

    def test_admin_stats(self):
        self.login_admin()
        response = self.client.get('/admin/stats')
        self.assertEqual(response.status_code, 200)

    def test_admin_file_versions(self):
        self.login_admin()
        response = self.client.get(f'/admin/file/{self.file.id}/versions')
        self.assertEqual(response.status_code, 200)

    def test_admin_file_access_logs(self):
        self.login_admin()
        response = self.client.get(f'/admin/file/{self.file.id}/access-logs')
        self.assertEqual(response.status_code, 200)

    def test_admin_user_activity(self):
        self.login_admin()
        response = self.client.get(f'/admin/user/{self.user.id}/activity')
        self.assertEqual(response.status_code, 200)

    def test_admin_toggle_user_status(self):
        self.login_admin()
        response = self.client.post(f'/admin/user/{self.user.id}/toggle-status')
        self.assertEqual(response.status_code, 302)  # Redirect after success
        user = User.query.get(self.user.id)
        self.assertFalse(user.is_active)  # Status should be toggled

    def test_admin_delete_file(self):
        self.login_admin()
        response = self.client.post(f'/admin/file/{self.file.id}/delete')
        self.assertEqual(response.status_code, 302)  # Redirect after success
        file = File.query.get(self.file.id)
        self.assertIsNone(file)  # File should be deleted

    def test_admin_add_tag(self):
        self.login_admin()
        response = self.client.post(f'/admin/file/{self.file.id}/add-tag', data={'tag_name': 'test_tag'})
        self.assertEqual(response.status_code, 302)  # Redirect after success
        tag = FileTag.query.filter_by(name='test_tag').first()
        self.assertIsNotNone(tag)

    def test_admin_remove_tag(self):
        self.login_admin()
        # First add a tag
        tag = FileTag(name='test_tag', file_id=self.file.id, created_by=self.admin.id)
        db.session.add(tag)
        db.session.commit()
        
        response = self.client.get(f'/admin/file/{self.file.id}/remove-tag/{tag.id}')
        self.assertEqual(response.status_code, 302)  # Redirect after success
        tag = FileTag.query.get(tag.id)
        self.assertIsNone(tag)

if __name__ == '__main__':
    unittest.main() 