import functools, os, calendar

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for,
    send_from_directory
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
# from flaskr.database import get_db
from flaskr.models import Owner, Item, Order, PaidOrder, Category, Notification, Discount, Hour, User
from flaskr.database import db
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import statistics
import json, requests
from flask.json import jsonify

UPLOAD_FOLDER = 'flaskr/static/uploads/'
ALLOWED_EXTENSIONS = set( [ 'png', 'jpg', 'jpeg' ] )

bp = Blueprint( 'business', __name__, url_prefix='/business' )
# Paypal details

PP_OAUTH_KEY = 'AVTPAKHzpqt2-SK3Vn4hbVib2w08W4EMBDJsgPy8VMpTVTteI97ZKQgpvxthxl-N3V7KO3BuywPvnUjL'
PP_OAUTH_SECRET = 'EAoOD3WF1SM-VUNcmKhGp4dKOOEI13z_X1vm4DoZMHlDOebcpEgbgzWa8tQpOlz5tSzRL-QGPha9ZJc6'
PP_ACCESS_URL = 'https://api.sandbox.paypal.com/v1/oauth2/token'
PP_PAYOUT_URL = 'https://api.sandbox.paypal.com/v1/payments/payouts'
PP_ACCESS_TOKEN = 'A21AAFm2RzjprglvlIDjWdcZbjKe1McjlKZhtCUtJC5hsgGLWH5KtBDQrFOkRBOQTvXjcngZEhthZpsHIB1cOSheakmMbMbHQ'
PP_ACCESS_EXPIRE = datetime(2018, 10, 14, 19, 16, 2, 118596)

def request_token( ):
    # request access token for the first time or
    # if the token already expired
    global PP_ACCESS_TOKEN, PP_ACCESS_EXPIRE, PP_ACCESS_TOKEN
    if not PP_ACCESS_TOKEN or (PP_ACCESS_EXPIRE and PP_ACCESS_EXPIRE < datetime.now( ) ):
        sess = requests.Session( )
        sess.auth = (PP_OAUTH_KEY, PP_OAUTH_SECRET)
        body = {
            'grant_type': 'client_credentials'
        }
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'Accept-Language': 'en_US'
        }
        r = sess.post( PP_ACCESS_URL, data=body, headers=headers )
        print( r.status_code )
        print( r.json( ) )
        if r.status_code != 200:
            return 'Paypal OAuth failed'
        data = r.json( )
        PP_ACCESS_TOKEN = data[ 'access_token' ]
        PP_ACCESS_EXPIRE = datetime.now( ) + timedelta( seconds=data[ 'expires_in' ] )
    return None

@bp.route( '/register', methods=('GET', 'POST') )
def register( ):
    if g.owner and g.owner.id:
        return redirect( url_for( 'business.view_business' ) )

    if request.method == 'POST':
        name = request.form[ 'b_name' ]
        email = request.form[ 'email' ]
        password = request.form[ 'password' ]
        lng = request.form[ 'long' ] 
        lat = request.form[ 'lat' ]

        error = None
        if not name:
            error = 'Name is required'
        elif not email:
            error = 'Email is required'
        elif not password:
            error = 'Password is required'
        elif not lng or not lat:
            error = 'Location is required'
        else:
            try:
                lng = float( lng )
                lat = float( lat )
                owner = Owner( name, email, generate_password_hash( password ), lng, lat )

                db.session.add( owner )
                db.session.commit( )

                cat = Category( business=owner.id, name='Other' )
                db.session.add( cat )
                db.session.commit( )

                error = 'Your account has been created'
                session.clear( )
                session[ 'owner_id' ] = owner.id
                return redirect( url_for( 'business.view_business' ) )
            except IntegrityError:
                error = 'An account already exists with email {}'.format( email )
            except ValueError:
                error = 'Invalid coordinates'
        flash( error )
    return render_template('business/register.html')    

@bp.route( '/login', methods=('GET', 'POST') )
def login( ):
    if g.owner and g.owner.id:
        return redirect( url_for( 'business.view_business' ) )

    if request.method == 'POST':
        email = request.form[ 'email' ]
        password = request.form[ 'password' ]

        error = None
        if not email:
            error = 'Email is required'
        elif not password:
            error = 'Password is required'
        else:
            try:
                owner = Owner.query.filter_by( email=email ).one( )

                if check_password_hash( owner.password, password ):
                    session.clear( )
                    session[ 'owner_id' ] = owner.id
                    error = "You have successfully logged in"
                    return redirect( url_for( 'business.view_business' ) )

                else:
                    error = "Incorrect password"
            except NoResultFound:
                error = "Incorrect email"

        flash( error )
    return render_template( 'business/login.html' )

@bp.route( '/logout' )
def logout( ):
    session.clear( )
    return redirect( url_for( 'index' ) )

@bp.before_app_request
def load_logged_in_user( ):
    owner_id = session.get( 'owner_id' )

    if owner_id is None:
        g.owner = None
    else:
        try:
            g.owner = Owner.query.filter_by( id=owner_id ).one( )
        except NoResultFound:
            g.owner = None
            session.clear( )

def login_required( view ):
    @functools.wraps( view )
    def wrapped_view( **kwargs ):
        print( g.owner )
        if g.owner is None:
            return redirect( url_for( 'business.login' ) )
        return view( **kwargs )
    return wrapped_view 

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route( '/items/modify/<int:i_id>', methods=[ 'POST' ] )
@login_required
def item_modify( i_id ):
    item = Item.query.filter_by( id=i_id, owner=g.owner.id )
    if not item.one_or_none( ):
        flash( 'Invalid item id' )
        return redirect( url_for( 'business.view_business' ) ) 

    name = request.form[ 'name' ]
    desc = request.form[ 'desc' ]
    price = request.form[ 'price' ]
    time = request.form[ 'time' ]
    cat = request.form[ 'category' ]

    error = None
    if not name:
        error = 'Item Name is required'
    elif not desc:
        error = 'Description is required'
    elif not price:
        error = 'Price is required'
    elif not time:
        error = 'Estimated Time is required'
    else:
        try:
            price = float( price )
            time = int( time )
            cat = int(cat)

            if price < 0:
                error = 'Invalid price'
            elif time < 0:
                error = 'Invalid time estimate'
            else:
                visible = 'visible' in request.form
                item.update( {
                    'name': name,
                    'desc': desc,
                    'price': price,
                    'time_estimate': time,
                    'visibility': visible, 
                    'category': cat
                } )
                db.session.commit( )

                file = None
                if 'file' in request.files:
                    file = request.files[ 'file' ]
                    filename = 'item{}.jpg'.format( i_id )
                    file.save( os.path.join( UPLOAD_FOLDER , filename ) )
                error = 'Item modified successfully'
        except ValueError: 
            error = 'Invalid price or time estimate'
    flash( error )
    return redirect( url_for( 'business.products', b_id=g.owner.id ) )

@bp.route( '/items/create', methods=[ 'POST' ] )
@login_required
def item_create( ):
    if request.method == 'POST':
        name = request.form[ 'name' ]
        desc = request.form[ 'desc' ]
        price = request.form[ 'price' ]
        time = request.form[ 'time' ]
        cat = request.form[ 'category' ]

        print( request.form )

        error = None
        if not name:
            error = 'Item Name is required'
        elif not desc:
            error = 'Description is required'
        elif not price:
            error = 'Price is required'
        elif not time:
            error = 'Estimated Time is required'
        else:
            try:
                price = float( price )
                time = int( time )
                #print("Catergory is ID "+cat)
                cat = int(cat)

                if price < 0:
                    error = 'Invalid price'
                elif time < 0:
                    error = 'Invalid time estimate'
                else:
                    item = Item( owner=g.owner.id, name=name, desc=desc, price=price, time_estimate=time, category=cat )
                    db.session.add( item )
                    db.session.commit( )

                    file = None
                    if 'file' in request.files:
                        file = request.files[ 'file' ]
                        filename = 'item{}.jpg'.format( item.id )
                        file.save( os.path.join( UPLOAD_FOLDER , filename ) )
                    error = 'Item added successfully'
                    # print( error )
            except IntegrityError:
                error = 'Another item with name {} already exists'.format( name )
                db.session.rollback( )
            except ValueError: 
                error = 'Invalid price or time estimate'
        flash( error )
        return redirect( url_for( 'business.products', b_id=g.owner.id ) )
    return "Invalid location"

@bp.route( '/items/delete/<int:item_id>' )
@login_required
def item_delete( item_id ):
    error = None
    item = Item.query.filter_by( owner=g.owner.id, id=item_id ).one_or_none( )
    if not item:
        error = 'Item not found'
    else:
        name = item.name
        db.session.delete( item )
        db.session.commit( )
        error = 'Item {} has been deleted'.format( name )

    flash( error )
    return redirect( url_for( 'business.products', b_id=g.owner.id ) )
    
@bp.route( '/hours/create', methods=[ 'POST' ] )
@login_required
def hour_create( ):
    error = None
    if request.method == 'POST':
        day = request.form[ 'day' ]
        start = int(request.form[ 'start' ])
        end = int(request.form[ 'end' ])


        error = None
        if not day:
            error = 'Weekday is required'
        elif end < start:
            error = 'Error in hours!'
            db.session.rollback( )
        else:
            existed = Hour.query.filter_by( day=day, owner=g.owner.id ).all()
            if len(existed) == 2:
                error = 'Error: System only supports 2 timeframes of opening hours per day'
                db.session.rollback( )
            else:
                conflict = False
                for item in existed:
                    dt1 = datetime.strptime(item.start, '%I%p')
                    hour1 = dt1.hour
                    try:
                        dt2 = datetime.strptime(item.end, '%I%p')
                        hour2 = dt2.hour
                    except ValueError:
                        dt2 = datetime.strptime(item.end, '%I%p(next day)')
                        hour2 = dt2.hour + 24

                    if not (start < hour1 and end < hour1) and not (start > hour2 and end > hour2):
                        conflict = True
                        break
                if conflict:
                    error = 'Error: Conflict with existing opening hours for the day'
                    db.session.rollback( )
                else:
                    show_start = start
                    show_end = end
                        
                    if start == 0:
                        show_start = '12am' 
                    elif start < 12:
                        show_start = str(start)+'am' 
                    elif start == 12:
                        show_start = str(start)+'pm' 
                    else:
                        show_start = str(start-12)+'pm' 
                        

                    if end < 12:
                        show_end = str(end)+'am' 
                    elif end == 12:
                        show_end = str(end)+'pm' 
                    elif end > 12 and end < 24:
                        show_end = str(end-12)+'pm'
                    elif end == 24:
                        show_end = '12am(next day)'
                    else:
                        show_end = str(end-24)+'am(next day)' 
                    hour = Hour( owner=g.owner.id, day=day, start=show_start, end=show_end )
                    db.session.add( hour )
                    db.session.commit( )
        flash( error )
        return redirect( url_for( 'business.view_business' ) )
    return "Invalid location"


@bp.route( '/hours/delete/<int:hour_id>' )
@login_required
def hour_delete( hour_id ):
    error = None
    hour = Hour.query.filter_by( owner=g.owner.id, id=hour_id ).one_or_none( )
    if not hour:
        error = 'Hours not found'
    else:

        name = hour.day
        start = hour.start
        end = hour.end
        db.session.delete( hour )
        db.session.commit( )
        error = 'Opening hours for ' +  calendar.day_name[name] + ': ' + start + '-' + end + ' has been deleted'

    flash( error )
    return redirect( url_for( 'business.view_business' ) )

@bp.route( '/category/delete/<int:cat_id>' )
@login_required
def category_delete( cat_id ):
    error = None
    cat = Category.query.filter_by( business=g.owner.id, id=cat_id ).one_or_none( )
    if not cat:
        error = 'Category not found'
    elif cat.name == 'Other':
        error = 'Other category cannot be deleted.'
    else:
        # We need to firstly move all the items in the target category back to 'other'
        other = Category.query.filter_by( business=g.owner.id, name='Other' ).one_or_none( )
        if not other:
            error = 'Default "Other" category not found, category cannot be deleted.'
        else:
            items = Item.query.filter_by( category=cat_id ).all( )
            for itm in items:
                itm.category = other.id

            name = cat.name
            db.session.delete( cat )
            db.session.commit( )

            error = 'Category {} has been deleted'.format( name )

    flash( error )
    return redirect( url_for( 'business.products', b_id=g.owner.id ) )

@bp.route( '/category/create', methods=[ 'POST' ] )
@login_required
def category_create( ):
    if request.method == 'POST':
        
        name = request.form[ 'name' ]

        error = None
        if not name:
            error = 'Category Name is required'
        else:
            try:
                category = Category( business=g.owner.id, name=name)
                db.session.add( category )
                db.session.commit( )

                error = 'Category "{}" added successfully'.format(name)
                    # print( error )
            except IntegrityError:
                error = 'Another category with name {} already exists'.format( name )
                db.session.rollback( )
        flash( error )
        return redirect( url_for( 'business.products', b_id=g.owner.id ) )
    return "Invalid location"


# Individual view of a business
@bp.route( '/', methods=[ 'GET', 'POST' ] )
def view_business( ):
    b_id = g.owner.id
    place = Owner.query.filter_by( id=b_id ).one_or_none( )
    if not place:
        flash( 'Invalid business ' )
        if request.referrer:
            return redirect( request.referrer ) # return to referrer
        else:
            return url_for( 'index' )

    if request.method == 'POST':
        return redirect( url_for( 'business.register', create=False ), code=307 )
    else:
        items = Item.query.filter_by( owner=b_id ).all( )
        cats = Category.query.filter_by( business=b_id ).all( )
        hours = Hour.query.filter_by( owner=b_id ).order_by( Hour.day ).all()
        if g.owner == place:
            # if the viewer owns this business, we want to allow them to
            # modify their information and add items
            return render_template( 'business/item.html', items=items, place=place, hours = hours, owner=g.owner, cats=cats )
        else:
            return render_template( 'business/item.html', items=items, place=place, hours = hours, owner=None, cats=cats )

@bp.route( '/products/<int:b_id>', methods=[ 'GET', 'POST'  ] )
@login_required
def products( b_id ):
    if g.owner.id != b_id:
        error = 'You cannot modify a business you do not own'
        print( error )
        return redirect( url_for( 'business.view_business' ) )

    place = Owner.query.filter_by( id=b_id ).one_or_none( )
    if not place:
        flash( 'Invalid business ' )
        if request.referrer:
            return redirect( request.referrer ) # return to referrer
        else:
            return url_for( 'index' )

    if request.method == 'POST':
        return redirect( url_for( 'business.register', create=False ), code=307 )

    else:
        items = Item.query.filter_by( owner=b_id ).order_by( Item.id ).all( )
        cats = Category.query.filter_by( business=b_id ).order_by( Category.name ).all( )
        if g.owner == place:
            # if the viewer owns this business, we want to allow them to
            # modify their information and add items
            return render_template( 'business/product.html', items=items, place=place, owner=g.owner, cats=cats )
        else:
            return render_template( 'business/item.html', items=items, place=place, owner=None, cats=cats )

@bp.route( '/modify/<int:b_id>', methods=[ 'POST' ] )
@login_required
def modify( b_id ):
    if g.owner.id != b_id:
        error = 'You cannot modify a business you do not own'
        print( error )
        return redirect( url_for( 'business.view_business' ) )
    name = request.form[ 'b_name' ]
    email = request.form[ 'email' ]
    password = request.form[ 'password' ]
    lng = request.form[ 'long' ] 
    lat = request.form[ 'lat' ]
    new_pass = None
    if 'new_pass' in request.form:
        new_pass = request.form[ 'new_pass' ]

    print( "Long: {}, Lat: {}".format( lng, lat ) )

    error = None
    if not name:
        error = 'Name is required'
    elif not email:
        error = 'Email is required'
    elif not password:
        error = 'Password is required'
    elif not lng or not lat:
        error = 'Location is required'
    else:
        try:
            lng = float( lng )
            lat = float( lat )

            if check_password_hash( g.owner.password, password ):
                if new_pass:
                    owner = Owner.query.filter_by( id=g.owner.id ).update( {
                        'name': name,
                        'email': email,
                        'password': generate_password_hash( new_pass ),
                        'longitude': lng,
                        'latitude': lat
                    } )
                else:
                    owner = Owner.query.filter_by( id=g.owner.id ).update( {
                        'name': name,
                        'email': email,
                        'longitude': lng,
                        'latitude': lat
                    } )
                db.session.commit( )
                error = 'Your account information has been modified'
            else:
                error = 'Current password is incorrect'
        except ValueError:
            error = 'Invalid coordinates'
    flash( error )
    return redirect( url_for( 'business.view_business' ) )

@bp.route( 'orders', methods=['GET'] )
@login_required
def orders( ):
    error = None
    ords = None
    itmDict = { }
    itmLst = { }
    timeRemain = { }
    ords = PaidOrder.query.filter_by( business=g.owner.id ).all( )

    # Setup itemDict to contain Item row for each item in PaidOrders.
    for o in ords:
        if o.status == 1:
            timeDiff = (datetime.now( ) - o.time_accepted).total_seconds( )
            timeDiff = min( timeDiff, o.time_estimate )
            # timeDiff = int( min( 100 * ( timeDiff / o.time_estimate ), 100 ) )
            timeRemain[ o.id ] = timeDiff

        itmLst[ o.id ] = [ ]
        print( o.order_details.split( ',' ) )
        print( o.id )
        for itm_id in o.order_details.split( ',' ):
            i_id = int( itm_id )
            print( i_id )
            itmLst[ o.id ].append( i_id )
            if i_id not in itmDict:
                item = Item.query.filter_by( id=i_id ).one_or_none( )
                print( item )
                if item:
                    itmDict[ i_id ] = item

    flash(error)
    return render_template( 'business/orders.html', orders=ords, owner=g.owner, items=itmDict, 
        itmLst=itmLst, timeRemain=timeRemain )

@bp.route( 'orders/accept/<int:o_id>' )
@login_required
def accept_order( o_id ):
    error = None

    pord = PaidOrder.query.filter_by( business=g.owner.id, id=o_id ).one_or_none( )
    if not pord:
        error = 'Order does not exist'
    else:
        try:
            pord.time_estimate = int( request.args[ 'time' ] )
            pord.status = 1
            pord.time_accepted = datetime.now( )
            db.session.commit( )

            note = Notification( 
                'Your order has been accepted, it is estimated to be finished in {} seconds'.format( pord.time_estimate ),
                user=pord.user, 
                sender=g.owner.name )
            db.session.add( note )
            db.session.commit( )

            error = 'Order {} accepted'.format( o_id )
        except ValueError:
            error = 'Invalid time estimate'
        except KeyError:
            error = 'Time estimate not provided'

    flash( error )
    return redirect( url_for( 'business.orders' ) )

@bp.route( 'orders/complete/<int:o_id>' )
@login_required
def complete_order( o_id ):
    error = None

    pord = PaidOrder.query.filter_by( business=g.owner.id, id=o_id ).one_or_none( )
    if not pord:
        error = 'Order does not exist'
    else:
        pord.status = 2

        # calculate time based rating of a store
        time_complete = datetime.now( )
        time_diff = max( pord.time_estimate, abs( (pord.time_accepted - time_complete).total_seconds( ) ) )
        # how heavy we want to penalise for not being on time
        # increase = more penalty
        RATING_FACTOR = 1.25

        # print( f"Sec: {(pord.time_accepted - time_complete).total_seconds( )}, TD: {time_diff}, TE: {pord.time_estimate}" )
        pord.rating = min( 5, round( (5 / (time_diff / pord.time_estimate) ** RATING_FACTOR), 1 ) )
        db.session.commit( )

        owner = Owner.query.filter_by( id=g.owner.id ).one_or_none( )
        ordrs = PaidOrder.query.filter_by( business=g.owner.id ).all( )
        owner.time_rating = round( statistics.mean( [ o.rating for o in ordrs if o.rating ] ), 1 )
        # print( f"Result rating: {owner.time_rating}" )
        db.session.commit( )

        note = Notification( 
            'Your order is now complete',
            user=pord.user, 
            sender=g.owner.name )
        db.session.add( note )
        db.session.commit( )

        error = 'Order {} completed'.format( o_id )

    flash( error )
    return redirect( url_for( 'business.orders' ) )

@bp.route( '/geojson' )
def geojson( ):
    owners = Owner.query.all( )
    lst = [ ]
    for owner in owners:
        lst.append( {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [ owner.longitude, owner.latitude ]
            },
            'properties': {
                'title': owner.name,
                'id': owner.id,
                'desc': owner.name
            }
        } )
    return jsonify( {
        'type': 'FeatureCollection',
        'features': lst
    } )

@bp.route('/testEnd')
def ords():
    
    ords = PaidOrder.query.filter_by( business=g.owner.id ).all()

    res_list = []
    for o in ords:
        res_list.append(o.as_dict())

    return jsonify(res_list)

# Discounts

@bp.route( '/discounts' )
@login_required
def view_discounts( ):
    discounts = Discount.query.filter_by( business=g.owner.id ).all( )
    return render_template( 'business/discounts.html', discounts=discounts )

@bp.route( '/discounts/remove/<int:d_id>' )
@login_required
def discount_delete( d_id ):
    discount = Discount.query.filter_by( business=g.owner.id, id=d_id ).one_or_none( )
    if discount:
        db.session.delete( discount )
        db.session.commit( )
        error = 'Discount removed'
    else:
        error = 'Discount not found'
    flash( error )
    return redirect( url_for( 'business.view_discounts' ) )


@bp.route( '/discounts/add', methods=[ 'POST' ] )
@login_required
def add_discount( ):
    error = None
    visible = 'visible' in request.form

    code = request.form[ 'code' ]
    ttype = request.form[ 'ttype' ]
    target = None
    if 'target' in request.form:
        target = request.form[ 'target' ]
    dtype = request.form[ 'dtype' ]
    value = request.form[ 'value' ]

    uses = request.form[ 'uses' ]
    single_uses = request.form[ 'single_uses' ]

    if not code:
        error = 'Code not specified'
    elif not ttype:
        error = 'Target type not specified'
    elif not dtype:
        error = 'Discount type not specified'
    elif not value:
        error = 'Value not specified'
    elif not uses:
        error = 'Uses not specified'
    elif not single_uses:
        error = 'Single uses not specified'
    else:
        try:
            ttype = int( ttype )
            dtype = int( dtype )
            value = float( value )

            if target and ttype == 0:
                target = None

            discount = Discount.query.filter_by( business=g.owner.id, code=code ).one_or_none( )
            if discount:
                error = 'A discount already exists with specified code'
            elif ttype < 0 or ttype > 2:
                error = 'Target type is out of range'
            elif dtype < 0 or dtype > 1:
                error = 'Discount type is out of range'
            elif dtype == 0 and ( value < 0 or value > 100 ):
                error = 'Percentage discount must be between 0 and 100'
            elif dtype == 1 and ( value < 0 ):
                error = 'Flat discount must be greater than 0'
            elif ttype != 0 and not target:
                error = 'Target not specified'
            else:
                ttype += 1
                discount = Discount( business=g.owner.id, visibility=visible, code=code, ttype=ttype, 
                    target=target, dtype=dtype, value=value, uses=uses, single_uses=single_uses )
                db.session.add( discount )
                db.session.commit( )
                print( ( visible, code, ttype, target, dtype, value ) )
        except ValueError:
            error = 'Invalid numeric value provided for value, target type or discount type'
    flash( error )
    return redirect( url_for( 'business.view_discounts' ) )


#Analytics stuff
@bp.route( '/analytics', methods=[ 'POST',"GET" ] )
@login_required
def analytics( ):
    error = None
    
    #get all the orders from THIS date
    #cur_date = str(datetime.now()+timedelta(days=1)+timedelta(days=-1))
    cur_date = str(datetime.now())
    cur_date = cur_date[:10]
    orders = PaidOrder.query.filter(PaidOrder.business == g.owner.id, PaidOrder.time_created.startswith(cur_date), or_(PaidOrder.status == 1, PaidOrder.status == 2) ).all()
    count = 0
    total = 0
    itemcount = {}
    itmDict = {}

    for o in orders:
        count = count + 1
        total = total + o.total
        for i_id in o.order_details.split( ',' ):
            if i_id not in itemcount.keys():
                itemcount[i_id] = 1
            else:
                itemcount[i_id] = itemcount[i_id]+1
            if i_id not in itmDict:
                item = Item.query.filter_by( id=i_id ).one_or_none( )
                if item:
                    itmDict[ i_id ] = item

    res = sorted(itemcount.items(), key=lambda x: -x[1])

    week_performance = []
    for i in range(7):
        date = str(datetime.now()+timedelta(days=-6+i))
        date = date[:10]
        ordz = PaidOrder.query.filter(PaidOrder.business == g.owner.id, PaidOrder.time_created.startswith(date), or_(PaidOrder.status == 1, PaidOrder.status == 2) ).all()
        if ordz:
            cur_total = 0
            for o in ordz:
                cur_total = cur_total + o.total
            week_performance.append(date+" = $"+str(cur_total))
        else:
            week_performance.append(date+" = $0")


    if count == 0:
        val_per_order = 0
    else:
        val_per_order = total/count
        val_per_order = round(val_per_order, 2)

    return render_template( 'business/analytics.html', week_performance=week_performance, today_num_items=res, item_dict=itmDict, val_per=val_per_order, count=count, todayData=orders)

#Analytics stuff
@bp.route('/order_search/', defaults={'page': 1})
@bp.route( '/order_search/<int:page>', methods=[ 'POST',"GET" ] )
@login_required
def order_search(page):
    per_page = 10
    error = None
    itmDict = {}
    prev = False
    next = False
    items = Item.query.filter_by( owner=g.owner.id ).all()


    if page == 0:
        next = True
        prev = False

    if request.method == 'POST':
        name = request.form[ 'name' ]
        desc = request.form[ 'desc' ]
        price = request.form[ 'price' ]
        time = request.form[ 'time' ]
        cat = request.form[ 'category' ]

    orders = PaidOrder.query.filter(PaidOrder.business == g.owner.id ).all()
    max_size = len(orders)

    orders = orders[ ((page-1)*per_page):((page-1)*per_page + per_page) ]

    for o in orders:
        for i_id in o.order_details.split( ',' ):
            if i_id not in itmDict:
                item = Item.query.filter_by( id=i_id ).one_or_none( )
                if item:
                    itmDict[ i_id ] = item



    return render_template( 'business/order_search.html', page=page, orders=orders, item_dict=itmDict, items=items, max_size=max_size, per_page=per_page)

@bp.route( '/order_search_results', methods=[ 'POST',"GET" ] )
@login_required
def order_search_results():
    if request.method == 'POST':
        itmDict = {}
        #orders = PaidOrder.query.filter(PaidOrder.business == g.owner.id ).all()
        orders = PaidOrder.query.filter(PaidOrder.business == g.owner.id, or_(PaidOrder.status == 1, PaidOrder.status == 2) )

        name = request.form[ 'name' ]
        date = request.form[ 'date' ]
        cost = request.form[ 'cost' ]
        item = request.form[ 'item' ]
        orderby = request.form[ 'orderby' ]

    
        if name != "":
            user_id = User.query.filter_by( name=name ).one_or_none( )
            if user_id == None:
                return render_template( 'business/order_search_results.html', orders=None)
            else:
               orders = orders.filter_by( user=user_id.id )

        if date != "":
            print("date is "+date)
            orders = orders.filter( PaidOrder.time_created.startswith(date) )
            if len(orders.all()) == 0:
                return render_template( 'business/order_search_results.html', orders=None)

        if cost != "":
                print("cost is "+cost)
                orders = orders.filter_by( total=cost )
                if len(orders.all()) == 0:
                    return render_template( 'business/order_search_results.html', orders=None)

        if item:
            print(item)
            orders = orders.filter( PaidOrder.order_details.contains(item) )

        if orderby:
            if orderby == "cost":
                orders = orders.order_by( PaidOrder.total.desc() )
            else:
                orders = orders.order_by( PaidOrder.time_created.desc() )

    #build an item dictionary to show item names
    for o in orders:
        for i_id in o.order_details.split( ',' ):
            if i_id not in itmDict:
                item = Item.query.filter_by( id=i_id ).one_or_none( )
                if item:
                    itmDict[ i_id ] = item

    return render_template( 'business/order_search_results.html', orders=orders , item_dict=itmDict)


# Notifications

@bp.route( '/notifications' )
@login_required
def get_notifications( ):
    note = Notification.query.filter_by( business=g.owner.id ).all( )
    res = [ ]
    for n in note:
        res.append( {
            'id': n.id,
            'sender': n.sender,
            'link': n.link,
            'msg': n.message
        } )
    return jsonify( res )

@bp.route( '/notifications/remove/<int:n_id>' )
@login_required
def remove_notification( n_id ):
    note = Notification.query.filter_by( business=g.owner.id, id=n_id ).one_or_none( )
    if note:
        db.session.delete( note )
        db.session.commit( )
        return 'Notification removed successfully'
    return 'Notification not found'

# Locate

@bp.route( '/locate/<int:o_id>' )
@login_required
def locate( o_id ):
    ordr = PaidOrder.query.filter_by( id=o_id, business=g.owner.id ).one_or_none( )
    dist = -1
    if ordr:
        dist = ordr.dist
    return jsonify({
        'dist': dist
    })

# Payment
@bp.route( '/request-payment' )
@login_required
def request_payment( ):
    ordr = PaidOrder.query.filter_by( business=g.owner.id, status=2 ).all( )
    if ordr:
        total = 0
        for o in ordr:
            total += o.total

        res = request_token( )
        if not res:
            flash( res )

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + PP_ACCESS_TOKEN
            }
            data = json.dumps( {
                'sender_batch_header': {
                    'sender_batch_id': int((datetime.now() - datetime.utcfromtimestamp( 0 )).total_seconds()),
                    'email_subject': 'You have a payment from Stacc!',
                    'email_message': 'You have received a payment from Stacc! Thanks for using our service!'
                },
                'items': [ 
                    {
                        'recipient_type': 'EMAIL',
                        "note": "Thanks for using Stacc!",
                        'amount': {
                            'value': total,
                            'currency': 'AUD'
                        },
                        'receiver': g.owner.email
                    }
                ]
            } )
            res = requests.post( url=PP_PAYOUT_URL, data=data, headers=headers )
            print( 'Sending Data:' )
            print( data )
            print( 'Payment Request: ' )
            print( res.status_code )
            print( res.json( ) )
            if res.status_code == 201 or res.status_code == 200:
                for o in ordr:
                    o.status = 3
                    db.session.commit( )
                flash( 'Payment has been sent via email' )
            else:
                flash( 'An error has occurred during payment' )
        else:
            flash( res )
    else:
        flash( 'There are no orders to be paid' )
    if request.referrer:
        return redirect( request.referrer ) # return to referrer
    else:
        return url_for( 'index' )
