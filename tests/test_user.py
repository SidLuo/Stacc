import pytest
from flask import g, session
from flaskr.models import User
from werkzeug.security import check_password_hash

def test_register( client, session ):
    assert client.get( '/user/register' ).status_code == 200
    response = client.post(
        '/user/register', data={ 'email': 'a', 'name': 'a', 'password': 'a' }
    )
    assert b'Your account has been created' in response.data
    user = User.query.filter_by( email='a', name='a' ).one( )
    assert user
    assert check_password_hash( user.password, 'a' )

    # these users should not exist
    assert not User.query.filter_by( email='a', name='b' ).one_or_none( )
    assert not User.query.filter_by( email='b', name='b' ).one_or_none( )
    assert not User.query.filter_by( email='b', name='a' ).one_or_none( )

@pytest.mark.parametrize( ('name', 'email', 'password', 'message' ), (
    ( '', 'a', 'b', b'Name is required' ),
    ( 'a', '', 'b', b'Email is required' ),
    ( 'a', 'a', '', b'Password is required' ),
    ( 'a', 'a', 'ok', b'already exists' ),
) )
def test_register_validate_input( client, name, email, password, message ):
    response = client.post( 
        '/user/register',
        data={ 'name': name, 'email': email, 'password': password }
    )
    assert message in response.data

def test_login( client ):
    response = client.post( 
        '/user/login',
        data={ 'email': 'a', 'password': 'a' }
    )
    assert response.status_code == 302
    user = User.query.filter_by( email='a', name='a' ).one( )
    with client.session_transaction() as session:
        assert 'user_id' in session # make sure users have user_id in session
        assert session[ 'user_id' ] == user.id

@pytest.mark.parametrize( ( 'email', 'password', 'message' ), (
    ( '', 'a', b'Email is required' ),
    ( 'a', '', b'Password is required' ),
    ( 'zzzz', 'a', b'Incorrect email' ),
    ( 'a', 'zzzz', b'Incorrect password' ),
) )
def test_login_validate_input( client, email, password, message ):
    response = client.post( 
        '/user/login',
        data={ 'email': email, 'password': password }
    )
    print( response.data )
    assert message in response.data