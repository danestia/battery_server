from sqlalchemy import text

def test_engine_exists(test_engine):
    assert test_engine is not None

def test_session_executes_sql(db_session):
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1