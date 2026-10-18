import pytest
from app.books import services as book_services
from app.models.book import BookCategory, BookCondition, ExchangeStatus, Book


def test_create_book_service(app, student_a):
    with app.app_context():
        book = book_services.create_book(
            owner=student_a,
            data={
                'title': 'Operating System Concepts',
                'author': 'Silberschatz, Galvin',
                'category': BookCategory.COMPUTER_SCIENCE,
                'condition': BookCondition.LIKE_NEW,
                'description': '10th Edition dinosaur book',
                'isbn': '9781119456339'
            }
        )
        assert book.id is not None
        assert book.owner_name == student_a.full_name
        assert book.owner_id == student_a.id
        assert book.exchange_status == ExchangeStatus.AVAILABLE


def test_list_books_search_and_filter(app, student_a):
    with app.app_context():
        book_services.create_book(
            owner=student_a,
            data={
                'title': 'Digital Logic Design',
                'author': 'Morris Mano',
                'category': BookCategory.ELECTRONICS,
                'condition': BookCondition.GOOD
            }
        )
        book_services.create_book(
            owner=student_a,
            data={
                'title': 'Advanced Calculus',
                'author': 'Wilfred Kaplan',
                'category': BookCategory.MATHEMATICS,
                'condition': BookCondition.FAIR
            }
        )

        # Search by title
        items, total, _ = book_services.list_books(search='Digital')
        assert total == 1
        assert items[0].title == 'Digital Logic Design'

        # Filter by category
        items_cat, total_cat, _ = book_services.list_books(category=BookCategory.MATHEMATICS)
        assert total_cat == 1
        assert items_cat[0].category == BookCategory.MATHEMATICS


from app.extensions import db


def test_owner_edit_book(app, student_a, sample_book):
    with app.app_context():
        b = db.session.get(Book, sample_book.id)
        updated = book_services.update_book(
            book=b,
            user=student_a,
            data={'title': 'Algorithms Unlocked - 2nd Edition'}
        )
        assert updated.title == 'Algorithms Unlocked - 2nd Edition'


def test_non_owner_cannot_edit_book(app, student_b, sample_book):
    with app.app_context():
        b = db.session.get(Book, sample_book.id)
        with pytest.raises(book_services.BookServiceError) as exc_info:
            book_services.update_book(
                book=b,
                user=student_b,
                data={'title': 'Hacked Title'}
            )
        assert exc_info.value.status_code == 403


def test_delete_book(app, student_a, sample_book):
    with app.app_context():
        b = db.session.get(Book, sample_book.id)
        book_services.delete_book(book=b, user=student_a)
        assert b.is_active is False
        assert book_services.get_book_by_id(sample_book.id) is None
