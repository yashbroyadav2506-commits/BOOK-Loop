from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.extensions import db, limiter
from app.books import books_bp
from app.books.forms import BookForm
from app.books import services as book_services
from app.upload_service import upload_book_cover
from app.models.book import BookCategory, BookCondition, ExchangeStatus, Book
from app.models.exchange_request import ExchangeRequest, RequestStatus
from app.models.user import User
from app.models.wishlist import Wishlist
from app.models.report import ListingReport, ReportStatus


@books_bp.route('/')
def index():
    recent_books, _, _ = book_services.list_books(
        sort_by='newest',
        page=1,
        per_page=6
    )
    return render_template(
        'index.html',
        recent_books=recent_books,
        categories=BookCategory.ALL,
        title='Pallotti BookLoop - Your Next Book Is Already Here'
    )


@books_bp.route('/marketplace')
@books_bp.route('/books')
def marketplace():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', 'All')
    condition = request.args.get('condition', 'All')
    status = request.args.get('status', 'All')
    semester = request.args.get('semester', 'All')
    sort_by = request.args.get('sort_by', 'newest')

    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1

    per_page = current_app.config['BOOKS_PER_PAGE']

    books, total, pages = book_services.list_books(
        search=search if search else None,
        category=category,
        condition=condition,
        exchange_status=status,
        semester=semester,
        sort_by=sort_by,
        page=page,
        per_page=per_page
    )

    semesters = [f"Semester {i}" for i in range(1, 9)]

    return render_template(
        'books.html',
        books=books,
        total=total,
        page=page,
        pages=pages,
        search=search,
        selected_category=category,
        selected_condition=condition,
        selected_status=status,
        selected_semester=semester,
        selected_sort=sort_by,
        categories=BookCategory.ALL,
        conditions=BookCondition.ALL,
        statuses=ExchangeStatus.ALL,
        semesters=semesters,
        title='Marketplace - Pallotti BookLoop'
    )


@books_bp.route('/books/<int:book_id>')
def book_detail(book_id: int):
    # Only admins or owners can see hidden books
    include_hidden = current_user.is_authenticated and current_user.is_admin
    book = book_services.get_book_by_id(book_id, include_hidden=include_hidden)
    
    if not book:
        # Check if owned by current user
        if current_user.is_authenticated:
            book = Book.query.filter_by(id=book_id, owner_id=current_user.id, is_active=True).first()

    if not book:
        flash('Book listing not found or has been hidden by moderators.', 'warning')
        return redirect(url_for('books.marketplace'))

    user_active_request = None
    user_available_books = []

    if current_user.is_authenticated:
        if current_user.id != book.owner_id:
            user_active_request = ExchangeRequest.query.filter(
                ExchangeRequest.book_id == book.id,
                ExchangeRequest.requester_id == current_user.id,
                ExchangeRequest.status.in_([RequestStatus.PENDING, RequestStatus.ACCEPTED])
            ).first()

            user_available_books = Book.query.filter_by(
                owner_id=current_user.id,
                is_active=True,
                exchange_status=ExchangeStatus.AVAILABLE
            ).all()

    return render_template(
        'book_detail.html',
        book=book,
        user_active_request=user_active_request,
        user_available_books=user_available_books,
        title=f'{book.title} - Pallotti BookLoop'
    )


@books_bp.route('/books/new', methods=['GET', 'POST'])
@login_required
def add_book():
    if not current_user.is_verified:
        flash('Please verify your college email address before listing a book. Check your inbox or click "Resend Verification" on your dashboard.', 'warning')
        return redirect(url_for('dashboard.index'))

    form = BookForm()
    if form.validate_on_submit():
        cover_url = form.cover_image_url.data.strip() if form.cover_image_url.data else None

        # Check for uploaded cover image file
        if form.cover_image_file.data:
            success, result_url_or_err = upload_book_cover(form.cover_image_file.data)
            if success:
                cover_url = result_url_or_err
            else:
                flash(f"Image upload notice: {result_url_or_err}", "warning")

        data = {
            'title': form.title.data,
            'author': form.author.data,
            'category': form.category.data,
            'condition': form.condition.data,
            'semester': form.semester.data,
            'description': form.description.data,
            'isbn': form.isbn.data,
            'cover_image_url': cover_url,
        }
        try:
            book = book_services.create_book(owner=current_user, data=data)
            flash(f'"{book.title}" was listed successfully in the marketplace!', 'success')
            return redirect(url_for('books.book_detail', book_id=book.id))
        except book_services.BookServiceError as e:
            flash(e.message, 'danger')

    return render_template(
        'add_book.html',
        form=form,
        is_edit=False,
        title='List a Book - Pallotti BookLoop'
    )


@books_bp.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id: int):
    book = db.session.get(Book, book_id)
    if not book or not book.is_active:
        flash('Book not found.', 'warning')
        return redirect(url_for('books.marketplace'))

    if book.owner_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to edit this listing.', 'danger')
        return redirect(url_for('books.book_detail', book_id=book.id))

    form = BookForm(obj=book)
    if form.validate_on_submit():
        cover_url = form.cover_image_url.data.strip() if form.cover_image_url.data else None

        if form.cover_image_file.data:
            success, result_url_or_err = upload_book_cover(form.cover_image_file.data)
            if success:
                cover_url = result_url_or_err
            else:
                flash(f"Image upload notice: {result_url_or_err}", "warning")

        data = {
            'title': form.title.data,
            'author': form.author.data,
            'category': form.category.data,
            'condition': form.condition.data,
            'semester': form.semester.data,
            'description': form.description.data,
            'isbn': form.isbn.data,
            'cover_image_url': cover_url or book.cover_image_url,
        }
        try:
            book_services.update_book(book=book, user=current_user, data=data)
            flash('Book listing updated successfully.', 'success')
            return redirect(url_for('books.book_detail', book_id=book.id))
        except book_services.BookServiceError as e:
            flash(e.message, 'danger')

    return render_template(
        'add_book.html',
        form=form,
        book=book,
        is_edit=True,
        title=f'Edit "{book.title}" - Pallotti BookLoop'
    )


@books_bp.route('/books/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_book(book_id: int):
    book = db.session.get(Book, book_id)
    if not book:
        flash('Book not found.', 'warning')
        return redirect(url_for('books.marketplace'))

    try:
        book_services.delete_book(book=book, user=current_user)
        flash('Book listing removed successfully.', 'info')
    except book_services.BookServiceError as e:
        flash(e.message, 'danger')

    return redirect(url_for('dashboard.index'))


@books_bp.route('/books/<int:book_id>/report', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def report_book(book_id: int):
    book = db.session.get(Book, book_id)
    if not book:
        flash('Book not found.', 'warning')
        return redirect(url_for('books.marketplace'))

    reason = request.form.get('reason', 'Inappropriate').strip()
    note = request.form.get('note', '').strip()

    report = ListingReport(
        reporter_id=current_user.id,
        book_id=book.id,
        reason=reason,
        note=note if note else None,
        status=ReportStatus.PENDING
    )
    try:
        db.session.add(report)
        db.session.commit()
        flash('Thank you. Your report has been submitted to campus moderators for review.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred submitting the report.', 'danger')

    return redirect(url_for('books.book_detail', book_id=book_id))


@books_bp.route('/students/<int:user_id>')
def student_profile(user_id: int):
    """Public student profile displaying only non-private info and active listings."""
    student = db.session.get(User, user_id)
    if not student or not student.is_active:
        flash('Student profile not found.', 'warning')
        return redirect(url_for('books.marketplace'))

    # Active, non-hidden books listed by this student
    books = Book.query.filter_by(
        owner_id=student.id,
        is_active=True,
        is_hidden=False
    ).order_by(Book.created_at.desc()).all()

    return render_template(
        'student_profile.html',
        student=student,
        books=books,
        title=f'{student.full_name} - Pallotti BookLoop'
    )


@books_bp.route('/wishlist', methods=['GET', 'POST'])
@login_required
def wishlist():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        isbn = request.form.get('isbn', '').strip()
        category = request.form.get('category', '').strip()

        if not title:
            flash('Please enter a book title or subject.', 'warning')
        else:
            w = Wishlist(
                user_id=current_user.id,
                title=title,
                isbn=isbn if isbn else None,
                category=category if category else None
            )
            try:
                db.session.add(w)
                db.session.commit()
                flash(f'Added "{title}" to your wishlist! You will be notified as soon as a student lists it.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving to wishlist: {str(e)}', 'danger')
        return redirect(url_for('books.wishlist'))

    my_wishlist = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.created_at.desc()).all()
    return render_template(
        'wishlist.html',
        wishlist=my_wishlist,
        categories=BookCategory.ALL,
        title='My Wishlist - Pallotti BookLoop'
    )


@books_bp.route('/wishlist/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_wishlist_item(item_id: int):
    item = db.session.get(Wishlist, item_id)
    if item and item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Wishlist item removed.', 'info')
    return redirect(url_for('books.wishlist'))
