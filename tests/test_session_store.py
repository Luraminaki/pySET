"""Tests for pyset.session_store.SessionStore."""

import logging
import threading
import time

import pytest

from pyset.modules.game.game import Game
from pyset.modules.game.set import Grid
from pyset.modules.misc.models import AppConfig
from pyset.session_store import GameSession, SessionStore


def _make_session(last_accessed: int | None = None) -> GameSession:
    now = int(time.time())
    return GameSession(
        game=Game(Grid()),
        game_secret='',
        created=now,
        last_accessed=now if last_accessed is None else last_accessed,
        ttl=1800,
    )


def test_starts_empty(session_store: SessionStore):
    assert len(session_store) == 0
    assert session_store.get('nope') is None


def test_create_if_missing_creates_a_session(session_store: SessionStore):
    session_store.create_if_missing('g1', _make_session)

    assert len(session_store) == 1
    assert session_store.get('g1') is not None


def test_create_if_missing_does_not_overwrite_an_existing_session(session_store: SessionStore):
    session_store.create_if_missing('g1', lambda: _make_session(last_accessed=111))
    session_store.create_if_missing('g1', lambda: _make_session(last_accessed=999))

    session = session_store.get('g1')
    assert session is not None
    assert session.last_accessed == 111


def test_create_if_missing_only_calls_factory_once_under_concurrency(session_store: SessionStore):
    call_count = 0
    count_lock = threading.Lock()

    def factory() -> GameSession:
        nonlocal call_count
        with count_lock:
            call_count += 1
        return _make_session()

    threads = [threading.Thread(target=session_store.create_if_missing, args=('same-id', factory)) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert call_count == 1
    assert len(session_store) == 1


def test_clear_removes_everything(session_store: SessionStore):
    session_store.create_if_missing('g1', _make_session)
    session_store.create_if_missing('g2', _make_session)
    assert len(session_store) == 2

    session_store.clear()

    assert len(session_store) == 0
    assert session_store.get('g1') is None
    assert session_store.get('g2') is None


def test_items_returns_a_snapshot_not_a_live_view(session_store: SessionStore):
    session_store.create_if_missing('g1', _make_session)

    snapshot = session_store.items()
    assert len(snapshot) == 1

    session_store.create_if_missing('g2', _make_session)

    assert len(snapshot) == 1
    assert len(session_store.items()) == 2


def test_is_full(session_store: SessionStore, app_config: AppConfig):
    for i in range(app_config.max_sessions):
        assert not session_store.is_full()
        session_store.create_if_missing(f'g{i}', _make_session)

    assert session_store.is_full()


def test_is_full_and_evict_inactive_read_config_live():
    config = AppConfig(max_sessions=1, session_ttl_seconds=1000)
    store = SessionStore(config=config, logger=logging.getLogger('test_session_store'))
    store.create_if_missing('g1', _make_session)

    assert store.is_full()

    # Mutating the config object after construction must take effect immediately -- SessionStore
    # must never snapshot these values at __init__ time (see the bug this regression-tests).
    config.max_sessions = 10
    assert not store.is_full()


def test_evict_inactive_is_a_noop_when_not_full(session_store: SessionStore):
    session_store.create_if_missing('stale', lambda: _make_session(last_accessed=0))

    session_store.evict_inactive()

    assert session_store.get('stale') is not None


def test_evict_inactive_removes_only_stale_sessions_once_full(app_config: AppConfig):
    config = AppConfig(max_sessions=2, session_ttl_seconds=100)
    store = SessionStore(config=config, logger=logging.getLogger('test_session_store'))
    store.create_if_missing('stale', lambda: _make_session(last_accessed=0))
    store.create_if_missing('fresh', lambda: _make_session(last_accessed=int(time.time())))
    assert store.is_full()

    store.evict_inactive()

    assert store.get('stale') is None
    assert store.get('fresh') is not None


def test_locked_yields_none_for_a_missing_session(session_store: SessionStore):
    with session_store.locked('nope') as session:
        assert session is None


def test_locked_yields_the_session_when_found(session_store: SessionStore):
    session_store.create_if_missing('g1', _make_session)

    with session_store.locked('g1') as session:
        assert session is not None


def test_locked_releases_the_lock_even_if_the_body_raises(session_store: SessionStore):
    session_store.create_if_missing('g1', _make_session)

    with pytest.raises(ValueError, match='boom'), session_store.locked('g1') as session:
        assert session is not None
        raise ValueError('boom')

    session = session_store.get('g1')
    assert session is not None
    acquired = session.lock.acquire(blocking=False)
    assert acquired, 'lock was not released after an exception inside the `with` block'
    session.lock.release()


def test_locked_serializes_concurrent_access_to_the_same_session(session_store: SessionStore):
    session_store.create_if_missing('g1', _make_session)

    order: list[str] = []
    first_holder_is_in = threading.Event()
    release_first_holder = threading.Event()

    def hold_the_lock():
        with session_store.locked('g1') as session:
            assert session is not None
            order.append('first-in')
            first_holder_is_in.set()
            release_first_holder.wait(timeout=5)
        order.append('first-out')

    def try_to_acquire_afterwards():
        assert first_holder_is_in.wait(timeout=5)
        with session_store.locked('g1') as session:
            assert session is not None
            order.append('second-in')

    first_thread = threading.Thread(target=hold_the_lock)
    second_thread = threading.Thread(target=try_to_acquire_afterwards)

    first_thread.start()
    assert first_holder_is_in.wait(timeout=5)
    second_thread.start()
    time.sleep(0.1)  # give the second thread a chance to block on the (still held) lock

    assert order == ['first-in'], 'the second thread must not enter while the first still holds the lock'

    release_first_holder.set()
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)

    assert order == ['first-in', 'first-out', 'second-in']


def test_touch_updates_last_accessed(session_store: SessionStore):
    session_store.create_if_missing('g1', lambda: _make_session(last_accessed=0))
    session = session_store.get('g1')
    assert session is not None
    assert session.last_accessed == 0

    SessionStore.touch(session)

    assert session.last_accessed > 0
