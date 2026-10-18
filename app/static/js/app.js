/**
 * Pallotti BookLoop - Client-side Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Password Visibility Toggle
    const toggleBtns = document.querySelectorAll('.toggle-password-btn');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetInputId = btn.getAttribute('data-target');
            const input = document.getElementById(targetInputId);
            const icon = btn.querySelector('i');
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    if (icon) {
                        icon.classList.remove('bi-eye');
                        icon.classList.add('bi-eye-slash');
                    }
                } else {
                    input.type = 'password';
                    if (icon) {
                        icon.classList.remove('bi-eye-slash');
                        icon.classList.add('bi-eye');
                    }
                }
            }
        });
    });

    // 2. Open Library ISBN Lookup Helper
    const isbnBtn = document.getElementById('btn-lookup-isbn');
    const isbnInput = document.getElementById('isbn');
    const lookupStatus = document.getElementById('isbn-lookup-status');

    if (isbnBtn && isbnInput) {
        isbnBtn.addEventListener('click', async () => {
            const rawIsbn = isbnInput.value.trim().replace(/[-\s]/g, '');
            if (!rawIsbn) {
                showLookupStatus('Please enter an ISBN (10 or 13 digits) first.', 'warning');
                return;
            }

            showLookupStatus('Searching Open Library metadata...', 'info');
            isbnBtn.disabled = true;
            const originalBtnHtml = isbnBtn.innerHTML;
            isbnBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Fetching...';

            try {
                const bibKey = `ISBN:${rawIsbn}`;
                const response = await fetch(`https://openlibrary.org/api/books?bibkeys=${bibKey}&format=json&jscmd=data`);
                
                if (!response.ok) {
                    throw new Error('Network response from Open Library was not ok');
                }

                const data = await response.json();
                const bookData = data[bibKey];

                if (bookData) {
                    // Title
                    const titleField = document.getElementById('title');
                    if (titleField && (!titleField.value || confirm('Autofill title with Open Library data?'))) {
                        titleField.value = bookData.title || '';
                    }

                    // Authors
                    const authorField = document.getElementById('author');
                    if (authorField && bookData.authors && bookData.authors.length > 0) {
                        const authorNames = bookData.authors.map(a => a.name).join(', ');
                        if (!authorField.value || confirm('Autofill author(s) with Open Library data?')) {
                            authorField.value = authorNames;
                        }
                    }

                    // Cover image
                    const coverField = document.getElementById('cover_image_url');
                    if (coverField && bookData.cover) {
                        const coverUrl = bookData.cover.large || bookData.cover.medium || bookData.cover.small;
                        if (coverUrl) {
                            coverField.value = coverUrl;
                            const coverPreview = document.getElementById('cover-preview-img');
                            if (coverPreview) {
                                coverPreview.src = coverUrl;
                                coverPreview.classList.remove('d-none');
                            }
                        }
                    }

                    showLookupStatus('Metadata found and autofilled! You can review and adjust any field.', 'success');
                } else {
                    showLookupStatus('No book found in Open Library for this ISBN. You can continue filling in the details manually.', 'secondary');
                }
            } catch (err) {
                console.warn('Open Library lookup error:', err);
                showLookupStatus('Could not reach Open Library. Manual entry is completely supported.', 'secondary');
            } finally {
                isbnBtn.disabled = false;
                isbnBtn.innerHTML = originalBtnHtml;
            }
        });
    }

    function showLookupStatus(msg, type) {
        if (!lookupStatus) return;
        lookupStatus.className = `alert alert-${type} py-2 px-3 small mt-2 mb-0`;
        lookupStatus.textContent = msg;
        lookupStatus.classList.remove('d-none');
    }

    // 3. Cover URL preview on input
    const coverUrlInput = document.getElementById('cover_image_url');
    const coverPreviewImg = document.getElementById('cover-preview-img');
    if (coverUrlInput && coverPreviewImg) {
        coverUrlInput.addEventListener('input', () => {
            const val = coverUrlInput.value.trim();
            if (val.startsWith('http://') || val.startsWith('https://')) {
                coverPreviewImg.src = val;
                coverPreviewImg.classList.remove('d-none');
            } else {
                coverPreviewImg.classList.add('d-none');
            }
        });
    }

    // 4. Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 6000);
    });
});
