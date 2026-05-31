import pytest
from unittest.mock import patch, MagicMock


def _mock_response(json_data=None, raises_on_status=None):
    mock = MagicMock()
    if raises_on_status:
        mock.raise_for_status.side_effect = raises_on_status
    else:
        mock.raise_for_status = MagicMock()
    if json_data is not None:
        mock.json.return_value = json_data
    else:
        mock.json.side_effect = ValueError("not JSON")
    return mock


def test_known_status_strings_map_correctly():
    from quality_score import STATUS_SCORE_MAP
    assert STATUS_SCORE_MAP["ok"] == 1.0
    assert STATUS_SCORE_MAP["healthy"] == 1.0
    assert STATUS_SCORE_MAP["operational"] == 1.0
    assert STATUS_SCORE_MAP["up"] == 1.0
    assert STATUS_SCORE_MAP["green"] == 1.0
    assert STATUS_SCORE_MAP["degraded"] == 0.5
    assert STATUS_SCORE_MAP["warning"] == 0.5
    assert STATUS_SCORE_MAP["partial_outage"] == 0.5
    assert STATUS_SCORE_MAP["yellow"] == 0.5
    assert STATUS_SCORE_MAP["down"] == 0.0
    assert STATUS_SCORE_MAP["error"] == 0.0
    assert STATUS_SCORE_MAP["critical"] == 0.0
    assert STATUS_SCORE_MAP["major_outage"] == 0.0
    assert STATUS_SCORE_MAP["red"] == 0.0


def test_unknown_status_string_maps_to_zero():
    with patch("quality_score.requests.get", return_value=_mock_response(json_data={"status": "unknown_status"})), \
         patch("quality_score.push_to_gateway") as mock_push:
        from quality_score import fetch_and_push_quality_score
        result = fetch_and_push_quality_score("bork", "http://example.com/health")
        assert result == 0.0
        mock_push.assert_called_once()


def test_successful_fetch_pushes_score():
    with patch("quality_score.requests.get", return_value=_mock_response(json_data={"status": "ok"})), \
         patch("quality_score.push_to_gateway") as mock_push:
        from quality_score import fetch_and_push_quality_score
        result = fetch_and_push_quality_score("bork", "http://example.com/health")
        assert result == 1.0
        mock_push.assert_called_once()


def test_fetch_failure_does_not_push():
    from requests import ConnectionError as ReqConnError
    with patch("quality_score.requests.get", side_effect=ReqConnError("refused")), \
         patch("quality_score.push_to_gateway") as mock_push:
        from quality_score import fetch_and_push_quality_score
        result = fetch_and_push_quality_score("bork", "http://example.com/health")
        assert result is None
        mock_push.assert_not_called()


def test_non_200_does_not_push():
    from requests import HTTPError
    with patch("quality_score.requests.get",
               return_value=_mock_response(raises_on_status=HTTPError("503"))), \
         patch("quality_score.push_to_gateway") as mock_push:
        from quality_score import fetch_and_push_quality_score
        result = fetch_and_push_quality_score("bork", "http://example.com/health")
        assert result is None
        mock_push.assert_not_called()


def test_non_json_response_does_not_push():
    with patch("quality_score.requests.get", return_value=_mock_response(json_data=None)), \
         patch("quality_score.push_to_gateway") as mock_push:
        from quality_score import fetch_and_push_quality_score
        result = fetch_and_push_quality_score("bork", "http://example.com/health")
        assert result is None
        mock_push.assert_not_called()


def test_missing_status_key_does_not_push():
    with patch("quality_score.requests.get",
               return_value=_mock_response(json_data={"message": "ok"})), \
         patch("quality_score.push_to_gateway") as mock_push:
        from quality_score import fetch_and_push_quality_score
        result = fetch_and_push_quality_score("bork", "http://example.com/health")
        assert result is None
        mock_push.assert_not_called()


def test_case_insensitive_status_lookup():
    with patch("quality_score.requests.get", return_value=_mock_response(json_data={"status": "OK"})), \
         patch("quality_score.push_to_gateway") as mock_push:
        from quality_score import fetch_and_push_quality_score
        result = fetch_and_push_quality_score("bork", "http://example.com/health")
        assert result == 1.0
        mock_push.assert_called_once()


def test_refresh_all_quality_scores_calls_fetch_for_each_service():
    from flask import Flask
    test_app = Flask(__name__)

    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = [
        ("bork", "http://bork.example.com/health"),
        ("bork2", "http://bork2.example.com/health"),
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("quality_score.get_db", return_value=mock_conn), \
         patch("quality_score.fetch_and_push_quality_score") as mock_fetch:
        from quality_score import refresh_all_quality_scores
        refresh_all_quality_scores(test_app)
        assert mock_fetch.call_count == 2
        mock_fetch.assert_any_call("bork", "http://bork.example.com/health")
        mock_fetch.assert_any_call("bork2", "http://bork2.example.com/health")


def test_refresh_all_quality_scores_continues_on_individual_failure():
    from flask import Flask
    test_app = Flask(__name__)

    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = [
        ("bork", "http://bork.example.com/health"),
        ("bork2", "http://bork2.example.com/health"),
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("quality_score.get_db", return_value=mock_conn), \
         patch("quality_score.fetch_and_push_quality_score",
               side_effect=[Exception("first fails"), 0.5]) as mock_fetch:
        from quality_score import refresh_all_quality_scores
        refresh_all_quality_scores(test_app)  # must not raise
        assert mock_fetch.call_count == 2
