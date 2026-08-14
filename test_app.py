from app import BODY


def test_페이지에_배포됐다고_나온다():
    assert "배포됐습니다" in BODY
