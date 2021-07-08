from click import command, echo
from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext

# Initialize SQLAlchemy with no settings
db = SQLAlchemy( )

@command( "init-db" )
@with_appcontext
def init_db_command( ):
    from flaskr.models import User, Owner

    db.create_all( )
    echo( 'Initialized the database.' )


def init_app( app ):
    db.init_app( app )
    app.cli.add_command( init_db_command )