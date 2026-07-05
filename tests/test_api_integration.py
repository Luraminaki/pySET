"""End-to-end tests hitting the real Flask app (routing, JSON wire format, aliases)."""

import json

import pytest
from flask.testing import FlaskClient

from pyset.server_app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch) -> FlaskClient:
    monkeypatch.chdir(tmp_path)  # keep the rotating log file out of the repo

    config_path = tmp_path / 'config.json'
    config_path.write_text(
        json.dumps(
            {
                'service_id': 'pySET-itest',
                'version': '0.2.0',
                'MAX_SESSIONS': 5,
                'SESSION_NAME_MAX_CHARS': 36,
                'SESSION_TTL_SECONDS': 1800,
                'MAX_PLAYERS': 4,
                'PLAYER_NAME_MAX_CHARS': 12,
                'SUBMIT_TIMEOUT_SECONDS': 10,
                'PENALTY_TIMEOUT_SECONDS': 0,
                'secret': 'itest-secret',
            }
        )
    )

    app = create_app(str(config_path), scheme='http://', subdomain='localhost')
    app.config.update(TESTING=True)
    return app.test_client()


def test_get_config_endpoint_excludes_secret(client: FlaskClient):
    resp = client.get('/api/app/get_config/')
    data = resp.get_json()

    assert 'secret' not in data
    assert data['MAX_SESSIONS'] == 5


def test_full_game_flow_over_http(client: FlaskClient):
    resp = client.post('/api/app/init_set_game/', json={'gameID': 'itest', 'gameSecret': ''})
    assert resp.get_json()['status'] == 'SUCCESS'

    resp = client.post('/api/app/add_player/', json={'gameID': 'itest', 'name': 'alice'})
    body = resp.get_json()
    assert body['status'] == 'SUCCESS'
    assert body['players_stats'][0]['name'] == 'alice'

    resp = client.post('/api/app/change_game_state/', json={'gameID': 'itest', 'enablePause': False})
    body = resp.get_json()
    assert body['status'] == 'SUCCESS'
    assert body['game_state'] == 'RUNNING'
    # The grid deals >= 12 cards (in multiples of 3): it keeps drawing until at least one valid
    # set exists, so it isn't always exactly 4 rows.
    assert len(body['grid']) >= 4
    assert all(len(row) == 3 for row in body['grid'])

    resp = client.post('/api/app/get_hints/', json={'gameID': 'itest'})
    body = resp.get_json()
    assert body['status'] == 'SUCCESS'
    assert body['sets']


def test_delete_running_games_over_http(client: FlaskClient):
    client.post('/api/app/init_set_game/', json={'gameID': 'itest'})

    resp = client.post('/api/app/delete_running_games/', json={'secret': 'wrong'})
    assert resp.get_json()['error'] == 'NOT_ALLOWED'

    resp = client.post('/api/app/delete_running_games/', json={'secret': 'itest-secret'})
    assert resp.get_json()['status'] == 'SUCCESS'

    resp = client.get('/api/app/get_running_games/')
    assert resp.get_json()['games'] == []
