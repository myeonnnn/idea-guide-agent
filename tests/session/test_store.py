import shutil

import pytest

from app.session.store import SessionStore


@pytest.fixture
def store(tmp_path):
    return SessionStore(base_dir=tmp_path / "sessions")


def test_create_returns_session_with_generated_id(store):
    session = store.create(idea="반려동물 산책 매칭 앱")
    assert session.id
    assert session.idea == "반려동물 산책 매칭 앱"
    assert session.stage_index == 0
    assert session.stage_outputs == {}


def test_save_and_load_round_trip(store):
    session = store.create(idea="아이디어")
    session.stage_index = 2
    session.stage_outputs["market_research"] = {"summary": "요약"}
    store.save(session)

    loaded = store.load(session.id)
    assert loaded.id == session.id
    assert loaded.stage_index == 2
    assert loaded.stage_outputs == {"market_research": {"summary": "요약"}}


def test_load_missing_session_raises(store):
    with pytest.raises(FileNotFoundError):
        store.load("does-not-exist")


def test_save_updates_updated_at(store):
    session = store.create(idea="아이디어")
    first_updated_at = session.updated_at
    store.save(session)
    assert session.updated_at >= first_updated_at


def test_save_recreates_base_dir_if_deleted_after_construction(store):
    shutil.rmtree(store.base_dir)

    session = store.create(idea="아이디어")

    assert store.load(session.id).idea == "아이디어"
