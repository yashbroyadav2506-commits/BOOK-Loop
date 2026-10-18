from app.models.book import BookCategory, BookCondition


def test_api_auth_register_and_login(client):
    # Register via API
    reg_res = client.post('/api/v1/auth/register', json={
        'full_name': 'API Student',
        'college_email': 'api.student@stvincentngp.edu.in',
        'password': 'Password123',
        'confirm_password': 'Password123',
        'department': 'Computer Science & Engineering',
        'academic_year': '1st Year'
    })
    assert reg_res.status_code == 201
    assert reg_res.json['success'] is True
    assert reg_res.json['user']['college_email'] == 'api.student@stvincentngp.edu.in'

    # Check /me
    me_res = client.get('/api/v1/auth/me')
    assert me_res.status_code == 200
    assert me_res.json['user']['full_name'] == 'API Student'

    # Logout
    logout_res = client.post('/api/v1/auth/logout')
    assert logout_res.status_code == 200

    # Login
    login_res = client.post('/api/v1/auth/login', json={
        'college_email': 'api.student@stvincentngp.edu.in',
        'password': 'Password123'
    })
    assert login_res.status_code == 200
    assert login_res.json['success'] is True


def test_api_books_crud_and_search(client, student_a):
    # Log in as student_a
    client.post('/api/v1/auth/login', json={
        'college_email': student_a.college_email,
        'password': 'AlphaPass123'
    })

    # Create book
    create_res = client.post('/api/v1/books', json={
        'title': 'Discrete Mathematics and Its Applications',
        'author': 'Kenneth Rosen',
        'category': BookCategory.MATHEMATICS,
        'condition': BookCondition.LIKE_NEW,
        'description': '7th Edition with solved exercises',
        'isbn': '9780073383095'
    })
    assert create_res.status_code == 201
    book_id = create_res.json['data']['id']

    # Get book by id
    get_res = client.get(f'/api/v1/books/{book_id}')
    assert get_res.status_code == 200
    assert get_res.json['data']['title'] == 'Discrete Mathematics and Its Applications'

    # List books with search
    list_res = client.get('/api/v1/books?search=Discrete')
    assert list_res.status_code == 200
    assert len(list_res.json['data']) == 1

    # Update book
    patch_res = client.patch(f'/api/v1/books/{book_id}', json={
        'condition': BookCondition.GOOD
    })
    assert patch_res.status_code == 200
    assert patch_res.json['data']['condition'] == BookCondition.GOOD

    # Delete book
    del_res = client.delete(f'/api/v1/books/{book_id}')
    assert del_res.status_code == 200

    # Verify deleted
    get_after = client.get(f'/api/v1/books/{book_id}')
    assert get_after.status_code == 404


def test_api_exchange_workflow_and_dashboard(client, student_a, student_b, sample_book):
    # Student B logs in
    client.post('/api/v1/auth/login', json={
        'college_email': student_b.college_email,
        'password': 'BetaPass123'
    })

    # Student B requests book from Student A
    req_res = client.post('/api/v1/exchange-requests', json={
        'book_id': sample_book.id,
        'message': 'Would love to borrow or trade for this semester.'
    })
    assert req_res.status_code == 201
    request_id = req_res.json['data']['id']

    # Check dashboard summary for student B
    dash_b = client.get('/api/v1/dashboard/summary')
    assert dash_b.status_code == 200
    assert dash_b.json['data']['pending_outgoing'] == 1

    # Student B logs out, Student A logs in
    client.post('/api/v1/auth/logout')
    client.post('/api/v1/auth/login', json={
        'college_email': student_a.college_email,
        'password': 'AlphaPass123'
    })

    # Student A checks dashboard summary
    dash_a = client.get('/api/v1/dashboard/summary')
    assert dash_a.json['data']['pending_incoming'] == 1

    # Student A accepts the exchange request
    accept_res = client.patch(f'/api/v1/exchange-requests/{request_id}', json={
        'action': 'accept'
    })
    assert accept_res.status_code == 200
    assert accept_res.json['data']['status'] == 'Accepted'

    # Student A completes the exchange
    comp_res = client.patch(f'/api/v1/exchange-requests/{request_id}', json={
        'action': 'complete'
    })
    assert comp_res.status_code == 200
    assert comp_res.json['data']['status'] == 'Completed'
