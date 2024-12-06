import pytest
from project.books.models import Book
from project import db, app


@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory DB for testing
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

@pytest.mark.parametrize(
    "name,author,year_published,book_type,status",
    [
        ("Book A", "Author A", 2000, "Fiction", "available"),
        ("Book B", "Author B", 1999, "Non-Fiction", "checked out"),
        ("B" * 64, "A" * 64, 1999, "T" * 20, "S" * 20),
    ],
)
def test_book_creation_valid_data(test_client, name, author, year_published, book_type, status):
    with app.app_context():
        book = Book(name=name, author=author, year_published=year_published, book_type=book_type, status=status)
        db.session.add(book)
        db.session.commit()

        retrieved = Book.query.filter_by(name=name).first()
        assert retrieved is not None
        assert retrieved.name == name
        assert retrieved.author == author
        assert retrieved.year_published == year_published
        assert retrieved.book_type == book_type
        assert retrieved.status == status

def test_book_creation_default_status(test_client):
    with app.app_context():
        book = Book(name="Book", author="Author", year_published=1999, book_type="Fiction")
        db.session.add(book)
        db.session.commit()

        retrieved = Book.query.filter_by(name="Book").first()
        assert retrieved is not None
        assert retrieved.name == "Book"
        assert retrieved.author == "Author"
        assert retrieved.year_published == 1999
        assert retrieved.book_type == "Fiction"
        assert retrieved.status == "available"

def test_book_year_published_forward(test_client):
    with app.app_context():
        with pytest.raises(Exception):
            book = Book(name="Name", author="Author", year_published=3030, book_type="Fiction")
            db.session.add(book)
            db.session.commit()

@pytest.mark.parametrize(
    "name,author,year_published,book_type",
    [
        (None, "Author", 2000, "Fiction"),
        ("Book", None, 2000, "Fiction"),
        ("Book", "Author", None, "Fiction"),
        ("Book", "Author", 2000, None),
        (123, "Author", 2000, "Fiction"),
        ("Book", 123, 2000, "Fiction"),
        ("Book", "Author", "Not a Year", "Fiction"),
        ("Book", "Author", 2000, 123),
    ],
)
def test_book_creation_invalid_data(test_client, name, author, year_published, book_type):
    with app.app_context():
        with pytest.raises(Exception):
            book = Book(name=name, author=author, year_published=year_published, book_type=book_type)
            db.session.add(book)
            db.session.commit()

def test_invalid_book_duplicate_name(test_client):
    with app.app_context():
        book1 = Book(name="Unique Book", author="Jane Doe", year_published=2021, book_type="Non-Fiction")
        book2 = Book(name="Unique Book", author="John Smith", year_published=2022, book_type="Fiction")

        db.session.add(book1)
        db.session.commit()

        with pytest.raises(Exception):
            db.session.add(book2)
            db.session.commit()

@pytest.mark.parametrize(
    "name",
    [
        "-- or #",
        "\" OR 1 = 1 -- -",
        "'''''''''''UNION SELECT '2",
        "1' ORDER BY 1--+",
        "' UNION SELECT(columnname ) from tablename --",
        ",(select * from (select(sleep(10)))a)",
        "Test'; DROP TABLE books;--",
    ],
)
def test_sql_injection(test_client, name):
    with app.app_context():
        with pytest.raises(Exception):
            book = Book(name=name, author="Author", year_published=1999, book_type="Fiction")
            db.session.add(book)
            db.session.commit()

@pytest.mark.parametrize(
    "name",
    [
        "\"-prompt(8)-\"",
        "'-prompt(8)-'",
        "<img/src/onerror=prompt(8)>",
        "<script\\x20type=\"text/javascript\">javascript:alert(1);</script>",
        "<script src=1 href=1 onerror=\"javascript:alert(1)\"</script>",
        "<script>alert('Hacked!');</script>",
    ],
)
def test_javascript_injection(test_client, name):
    with app.app_context():
        with pytest.raises(Exception):
            book = Book(name=name, author="Author", year_published=1999, book_type="Fiction")
            db.session.add(book)
            db.session.commit()

@pytest.mark.parametrize(
    "name,author,year_published,book_type,status",
    [
        ("B" * 10000, "Author", 2000, "Fiction", "available"),
        ("B" * 100000, "Author", 2000, "Fiction", "available"),
        ("B" * 1000000, "Author", 2000, "Fiction", "available"),
        ("B" * 5000000, "Author", 2000, "Fiction", "available"),
        ("Book", "A" * 10000, 2000, "Fiction", "available"),
        ("Book", "A" * 100000, 2000, "Fiction", "available"),
        ("Book", "A" * 1000000, 2000, "Fiction", "available"),
        ("Book", "A" * 5000000, 2000, "Fiction", "available"),
        ("Book", "Author", 3000, "Fiction", "available"),
        ("Book", "Author", 100000, "Fiction", "available"),
        ("Book", "Author", 10000000, "Fiction", "available"),
        ("Book", "Author", 50000000, "Fiction", "available"),
        ("Book", "Author", 2000, "T" * 10000, "available"),
        ("Book", "Author", 2000, "T" * 100000, "available"),
        ("Book", "Author", 2000, "T" * 1000000, "available"),
        ("Book", "Author", 2000, "T" * 5000000, "available"),
        ("Book", "Author", 2000, "Fiction", "S" * 10000),
        ("Book", "Author", 2000, "Fiction", "S" * 10000),
        ("Book", "Author", 2000, "Fiction", "S" * 100000),
        ("Book", "Author", 2000, "Fiction", "S" * 1000000),
        ("Book", "Author", 2000, "Fiction", "S" * 5000000),
    ],
)
def test_extreme(test_client, name, author, year_published, book_type, status):
    with app.app_context():
        with pytest.raises(Exception):
            book = Book(name=name, author=author, year_published=year_published, book_type=book_type, status=status)
            db.session.add(book)
            db.session.commit()
