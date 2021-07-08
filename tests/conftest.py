import os, tempfile, pytest
from flaskr import create_app
from flaskr.database import db as _db
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

TESTDB = 'test.db'
TESTDB_PATH = '/tmp/project/data/{}'.format( TESTDB )
TESTDB_URI = 'sqlite:///' + TESTDB_PATH

@pytest.fixture( scope='session' )
def app( request ):
    return create_app( { 'TESTING': True } )

@pytest.fixture( scope='session' )
def db( app, request ):
    with app.app_context( ):
        _db.drop_all( )
        _db.create_all( )

@pytest.fixture( scope='function', autouse=True )
def session( app, db, request ):
    """Creates a new database session for a test."""

    with app.app_context( ):
        conn = _db.engine.connect( )
        txn = conn.begin( )

        options = dict( bind=conn, binds={ } )
        sess = _db.create_scoped_session( options=options )

        sess.begin_nested( )

        @event.listens_for( sess( ), 'after_transaction_end' )
        def restart_savepoint( sess2, trans ):
            if trans.nested and not trans._parent.nested:
                sess2.expire_all( )
                sess.begin_nested( )


        _db.session = sess
        yield sess

        sess.remove( )
        txn.rollback( )
        conn.close( )

@pytest.fixture
def client( app ):
    return app.test_client( )

@pytest.fixture
def runner( app ):
    return app.test_cli_runner( )


# # Auth Testing
# class AuthActions( object ):
#     def __init__( self, client ):
#         self._client = client

#     def login( self, email='test', password='test' ):
#         return self._client.post( 
#             '/auth/login',
#             data={ 'email': email, 'password': password }
#         )
    
#     def logout( self ):
#         return self._client.get( '/auth/logout' )

# @pytest.fixture
# def auth( client ):
#     return AuthActions( client )