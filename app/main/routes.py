from datetime import datetime, timezone
from flask import render_template, Response, request, flash, redirect, url_for
from app.main import main_bp
from app.models.book import Book


@main_bp.route('/about')
def about():
    return render_template(
        'pages/about.html',
        title='About Us - Pallotti BookLoop'
    )


@main_bp.route('/how-it-works')
def how_it_works():
    return render_template(
        'pages/how_it_works.html',
        title='How It Works - Pallotti BookLoop'
    )


@main_bp.route('/faq')
def faq():
    return render_template(
        'pages/faq.html',
        title='Frequently Asked Questions - Pallotti BookLoop'
    )


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Thank you for reaching out! A student coordinator will respond to your query soon.', 'success')
        return redirect(url_for('main.contact'))
    return render_template(
        'pages/contact.html',
        title='Contact & Support - Pallotti BookLoop'
    )


@main_bp.route('/terms')
def terms():
    return render_template(
        'pages/terms.html',
        title='Terms of Use - Pallotti BookLoop'
    )


@main_bp.route('/privacy')
def privacy():
    return render_template(
        'pages/privacy.html',
        title='Privacy Policy - Pallotti BookLoop'
    )


@main_bp.route('/robots.txt')
def robots_txt():
    content = """User-agent: *
Allow: /
Allow: /marketplace
Allow: /about
Allow: /how-it-works
Allow: /faq
Disallow: /admin/
Disallow: /dashboard/
Disallow: /api/

Sitemap: https://pallottibookloop.in/sitemap.xml
"""
    return Response(content, mimetype='text/plain')


@main_bp.route('/sitemap.xml')
def sitemap_xml():
    books = Book.query.filter_by(is_active=True, is_hidden=False).all()
    host = request.host_url.rstrip('/')

    static_urls = [
        f"{host}/",
        f"{host}/marketplace",
        f"{host}/about",
        f"{host}/how-it-works",
        f"{host}/faq",
        f"{host}/contact",
        f"{host}/terms",
        f"{host}/privacy",
    ]

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    for u in static_urls:
        xml.append(f'  <url><loc>{u}</loc><lastmod>{now}</lastmod><changefreq>weekly</changefreq></url>')

    for b in books:
        book_date = b.updated_at.strftime('%Y-%m-%d') if b.updated_at else now
        xml.append(f'  <url><loc>{host}/books/{b.id}</loc><lastmod>{book_date}</lastmod><changefreq>daily</changefreq></url>')

    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')
