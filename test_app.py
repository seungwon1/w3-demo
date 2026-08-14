from app import HEADLINE, page


def test_페이지에_헤드라인이_있다():
    assert HEADLINE in page()


def test_신청_버튼이_서버로_보낸다():
    assert 'action="/apply"' in page()
