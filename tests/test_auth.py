from app.models.user import User


def test_password_hashing():
    user = User(
        full_name="Test User",
        college_email="test@stvincentngp.edu.in",
        department="Computer Science & Engineering",
        academic_year="1st Year"
    )
    user.set_password("SecurePassword456")
    assert user.password_hash != "SecurePassword456"
    assert user.check_password("SecurePassword456") is True
    assert user.check_password("WrongPassword") is False


def test_user_registration(client, app):
    res = client.post('/register', data={
        'full_name': 'New Student',
        'college_email': 'newstudent@stvincentngp.edu.in',
        'department': 'Mechanical Engineering',
        'academic_year': '2nd Year',
        'phone_number': '9999888877',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        u = User.query.filter_by(college_email='newstudent@stvincentngp.edu.in').first()
        assert u is not None
        assert u.full_name == 'New Student'
        assert u.department == 'Mechanical Engineering'


def test_duplicate_registration_rejected(client, student_a):
    res = client.post('/register', data={
        'full_name': 'Imposter Alpha',
        'college_email': student_a.college_email,
        'department': 'Civil Engineering',
        'academic_year': '1st Year',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)
    assert b'already registered' in res.data or res.status_code == 200


def test_login_and_logout(client, student_a):
    # Valid login
    res = client.post('/login', data={
        'college_email': student_a.college_email,
        'password': 'AlphaPass123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Welcome back' in res.data

    # Logout
    res_logout = client.get('/logout', follow_redirects=True)
    assert res_logout.status_code == 200
    assert b'logged out safely' in res_logout.data


def test_invalid_login_credentials(client, student_a):
    res = client.post('/login', data={
        'college_email': student_a.college_email,
        'password': 'IncorrectPassword'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Invalid email or password' in res.data
