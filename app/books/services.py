from typing import Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy import or_
from app.extensions import db
from app.models.book import Book, BookCategory, BookCondition, ExchangeStatus
from app.models.user import User
from app.models.notification import Notification
from app.models.wishlist import Wishlist
from app.email_service import send_exchange_notification


class BookServiceError(Exception):
    """Custom exception for book service operations."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def list_books(
    search: Optional[str] = None,
    category: Optional[str] = None,
    condition: Optional[str] = None,
    exchange_status: Optional[str] = None,
    semester: Optional[str] = None,
    sort_by: str = 'newest',
    page: int = 1,
    per_page: int = 9,
    only_active: bool = True,
    include_hidden: bool = False
) -> Tuple[list[Book], int, int]:
    """
    Query books with search, filters, sorting, and pagination.
    Returns (items, total_count, total_pages).
    """
    query = Book.query

    if only_active:
        query = query.filter(Book.is_active.is_(True))

    if not include_hidden:
        query = query.filter(Book.is_hidden.is_(False))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Book.title.ilike(search_term),
                Book.author.ilike(search_term),
                Book.isbn.ilike(search_term),
                Book.description.ilike(search_term)
            )
        )

    if category and category != 'All':
        query = query.filter(Book.category == category)

    if condition and condition != 'All':
        query = query.filter(Book.condition == condition)

    if exchange_status and exchange_status != 'All':
        query = query.filter(Book.exchange_status == exchange_status)

    if semester and semester != 'All':
        query = query.filter(Book.semester == semester)

    if sort_by == 'oldest':
        query = query.order_by(Book.created_at.asc())
    elif sort_by == 'title':
        query = query.order_by(Book.title.asc())
    else:  # newest
        query = query.order_by(Book.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return pagination.items, pagination.total, pagination.pages


def get_book_by_id(book_id: int, include_hidden: bool = False) -> Optional[Book]:
    """Get active book by id."""
    query = Book.query.filter_by(id=book_id, is_active=True)
    if not include_hidden:
        query = query.filter_by(is_hidden=False)
    return query.first()


def notify_wishlist_students(book: Book) -> None:
    """Notify students who have this book or ISBN on their wishlist."""
    try:
        wishlist_matches = Wishlist.query.filter(
            Wishlist.user_id != book.owner_id,
            Wishlist.is_notified.is_(False),
            or_(
                Wishlist.title.ilike(f"%{book.title[:30]}%"),
                (Wishlist.isbn == book.isbn) if book.isbn else False
            )
        ).all()

        for wish in wishlist_matches:
            # Create in-app notification
            notif = Notification(
                user_id=wish.user_id,
                title="Wishlist Match Available!",
                message=f"'{book.title}' was just listed in the marketplace by {book.owner_name}.",
                link=f"/books/{book.id}"
            )
            db.session.add(notif)
            wish.is_notified = True

            # Send email
            if wish.user and wish.user.college_email:
                send_exchange_notification(
                    to_email=wish.user.college_email,
                    title=f"Wishlist Alert: '{book.title}' is now available!",
                    message=f"A fellow student ({book.owner_name}) has listed '{book.title}' on Pallotti BookLoop.",
                    action_url=f"/books/{book.id}"
                )
    except Exception:
        # Wishlist notification failure must not abort book creation
        pass


def create_book(owner: User, data: dict) -> Book:
    """
    Create a new book listing belonging to the authenticated user.
    Enforces email verification and sets owner.
    """
    if not owner.is_verified:
        raise BookServiceError("Please verify your college email address before listing textbooks.", status_code=403)

    title = (data.get('title') or '').strip()
    author = (data.get('author') or '').strip()
    category = (data.get('category') or '').strip()
    condition = (data.get('condition') or '').strip()
    description = (data.get('description') or '').strip()
    isbn = (data.get('isbn') or '').strip()
    cover_image_url = (data.get('cover_image_url') or '').strip()
    semester = (data.get('semester') or '').strip()

    if not title:
        raise BookServiceError("Book title is required.")
    if not author:
        raise BookServiceError("Book author is required.")
    if category not in BookCategory.ALL:
        raise BookServiceError(f"Invalid category. Choose from: {', '.join(BookCategory.ALL)}")
    if condition not in BookCondition.ALL:
        raise BookServiceError(f"Invalid condition. Choose from: {', '.join(BookCondition.ALL)}")

    book = Book(
        title=title,
        author=author,
        category=category,
        condition=condition,
        owner_name=owner.full_name,
        exchange_status=ExchangeStatus.AVAILABLE,
        description=description if description else None,
        isbn=isbn if isbn else None,
        cover_image_url=cover_image_url if cover_image_url else None,
        semester=semester if semester else None,
        owner_id=owner.id,
        is_active=True,
        is_hidden=False
    )

    try:
        db.session.add(book)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise BookServiceError(f"Database error saving book: {str(e)}", status_code=500)

    # Check and trigger wishlist alerts
    notify_wishlist_students(book)
    try:
        db.session.commit()
    except Exception:
        pass

    return book


def update_book(book: Book, user: User, data: dict) -> Book:
    """
    Update book listing. Only owner or admin is permitted.
    """
    if book.owner_id != user.id and not user.is_admin:
        raise BookServiceError("You are not authorized to edit this book.", status_code=403)

    title = data.get('title')
    if title is not None:
        title = title.strip()
        if not title:
            raise BookServiceError("Book title cannot be empty.")
        book.title = title

    author = data.get('author')
    if author is not None:
        author = author.strip()
        if not author:
            raise BookServiceError("Book author cannot be empty.")
        book.author = author

    category = data.get('category')
    if category is not None:
        if category not in BookCategory.ALL:
            raise BookServiceError(f"Invalid category. Choose from: {', '.join(BookCategory.ALL)}")
        book.category = category

    condition = data.get('condition')
    if condition is not None:
        if condition not in BookCondition.ALL:
            raise BookServiceError(f"Invalid condition. Choose from: {', '.join(BookCondition.ALL)}")
        book.condition = condition

    if 'semester' in data:
        book.semester = data['semester'].strip() if data['semester'] else None

    if 'description' in data:
        book.description = data['description'].strip() if data['description'] else None

    if 'isbn' in data:
        book.isbn = data['isbn'].strip() if data['isbn'] else None

    if 'cover_image_url' in data:
        book.cover_image_url = data['cover_image_url'].strip() if data['cover_image_url'] else None

    if 'exchange_status' in data:
        new_status = data['exchange_status']
        if new_status not in ExchangeStatus.ALL:
            raise BookServiceError("Invalid exchange status.")
        book.exchange_status = new_status

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise BookServiceError(f"Database error updating book: {str(e)}", status_code=500)

    return book


def delete_book(book: Book, user: User) -> None:
    """Soft-delete book. Only permitted if owner or admin."""
    if book.owner_id != user.id and not user.is_admin:
        raise BookServiceError("You are not authorized to delete this book.", status_code=403)

    if book.exchange_status in [ExchangeStatus.RESERVED, ExchangeStatus.EXCHANGED]:
        raise BookServiceError(
            f"Cannot delete a book that is currently {book.exchange_status}.",
            status_code=400
        )

    try:
        book.is_active = False
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise BookServiceError(f"Database error deleting book: {str(e)}", status_code=500)


def expire_stale_books() -> int:
    """
    Mark listings that have exceeded their 60-day expiry as Unavailable.
    Returns number of books expired.
    """
    now = datetime.now(timezone.utc)
    stale_books = Book.query.filter(
        Book.is_active.is_(True),
        Book.exchange_status == ExchangeStatus.AVAILABLE,
        Book.expires_at <= now
    ).all()

    count = 0
    for b in stale_books:
        b.exchange_status = ExchangeStatus.UNAVAILABLE
        count += 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise BookServiceError(f"Database error expiring stale books: {str(e)}", status_code=500)

    return count
