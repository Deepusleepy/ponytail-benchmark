def validate_user(u):
    assert "name" in u
    assert "age" in u
    return True