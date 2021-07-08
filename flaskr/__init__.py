import os
from flask import Flask, render_template, send_from_directory, send_file

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'flaskr.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        MAX_CONTENT_LENGTH=5 * 1024 * 1024
    )

    print( app.instance_path )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    
    @app.route( '/' )
    def idx( ):
        return render_template( 'base.html' )        

    from . import database
    database.init_app( app )

    from . import user, business
    app.register_blueprint( user.bp ) 
    app.register_blueprint( business.bp )

    UPLOAD_FOLDER = 'static/uploads/'
    @app.route( '/uploads/<filename>' )
    def uploaded_file( filename ):
        if os.path.isfile( os.path.join( 'flaskr/' + UPLOAD_FOLDER, filename ) ):
            return send_from_directory( UPLOAD_FOLDER, filename )
        else:
            return send_from_directory( UPLOAD_FOLDER, 'placeholder.png' )

    app.add_url_rule( '/', endpoint='index' )

    return app