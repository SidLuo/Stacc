import functools
from pyzomato import Pyzomato

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask, jsonify, json
)
from werkzeug.security import check_password_hash, generate_password_hash
# from flaskr.database import get_db
from flaskr.models import User, Owner, Order, Item, PaidOrder, Category, Notification, Rating, Discount, UserDiscount, Hour
from flaskr.database import db
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import hashlib
import statistics
import pprint

bp = Blueprint( 'user', __name__, url_prefix='/user' )

@bp.route( '/guest_create' )
def guest_create( ):
    # If they are already logged in, we don't create a new account
    if g.user:
        return redirect( url_for( 'user.home' ) )
    
    user = User( isguest=True, password='' )
    db.session.add( user )
    db.session.commit( )
    user.name = 'Guest{}'.format( user.id )
    db.session.commit( )

    session.clear( )
    session[ 'user_id' ] = user.id
    g.user = user
    error = 'You are now logged in as {}'.format( user.name )
    flash( error )

    return redirect( url_for( 'user.home' ) )

@bp.route( '/register', methods=('GET', 'POST') )
def register( ):
    if g.user and g.user.isguest == False:
        return redirect( url_for( 'user.home' ) )

    if request.method == 'POST':
        name = request.form[ 'name' ]
        email = request.form[ 'email' ]
        password = request.form[ 'password' ]

        error = None
        if not name:
            error = 'Name is required'
        elif not email:
            error = 'Email is required'
        elif not password:
            error = 'Password is required'
        else:
            try:
                if not g.user: # create new account
                    user = User( name, email, generate_password_hash( password ) )
                    db.session.add( user )
                    db.session.commit( )
                    session.clear( )
                    session[ 'user_id' ] = user.id
                    error = 'Your account has been created'
                    flash( error )
                    return redirect( url_for( 'user.home' ) )
                else: # modify existing guest account
                    if not User.query.filter_by( email=email ).one_or_none( ):
                        user = User.query.filter_by( id=g.user.id, isguest=True )
                        user.update( {
                            'name': name,
                            'email': email,
                            'password': generate_password_hash( password ),
                            'isguest': False
                        } )
                        error = 'Your guest account has been transferred'
                        db.session.commit( )
                        return redirect( url_for( 'users.home' ) )
                    else:
                        error = 'An account already exists with email {}'.format( email )
            except IntegrityError:
                error = 'An account already exists with email {}'.format( email )

        flash( error )
    return render_template('user/register.html')

@bp.route( '/login', methods=('GET', 'POST') )
def login( ):
    if g.user:
        return redirect( url_for( 'user.home' ) )

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
                user = User.query.filter_by( email=email ).one( )

                if check_password_hash( user.password, password ):
                    session.clear( )
                    session[ 'user_id' ] = user.id
                    error = 'You have successfully logged in'
                    return redirect( url_for( 'user.home' ) )

                else:
                    error = 'Incorrect password'
            except NoResultFound:
                error = 'Incorrect email'

        flash( error )
    return render_template( 'user/login.html' )

@bp.route( '/logout' )
def logout( ):
    session.clear( )
    return redirect( url_for( 'index' ) )

@bp.before_app_request
def load_logged_in_user( ):
    user_id = session.get( 'user_id' )
    if user_id is None:
        g.user = None
    else:
        try:
            g.user = User.query.filter_by( id=user_id ).one( )
        except NoResultFound:
            g.user = None
            session.clear( )

def login_required( view ):
    @functools.wraps( view )
    def wrapped_view( **kwargs ):
        if g.user is None:
            return redirect( url_for( 'user.login' ) )
        return view( **kwargs )
    return wrapped_view

@bp.route( '/' )
@login_required
def home( ):
    owners = Owner.query.all( )
    open = []
    now = datetime.now()
    day = now.weekday()
    for owner in list(owners):
        
        hours = Hour.query.filter_by( owner=owner.id, day=day ).all( )
        previous_ends = Hour.query.filter_by( owner=owner.id, day=(day-1) % 7 ).all( )
        
        for hour in hours:
            dt1 = datetime.strptime(hour.start, '%I%p')
            hour1 = dt1.hour
            try:
                dt2 = datetime.strptime(hour.end, '%I%p')
                hour2 = dt2.hour
            except ValueError:
                dt2 = datetime.strptime(hour.end, '%I%p(next day)')
                hour2 = dt2.hour + 24
            if now.hour >= hour1 and now.hour < hour2:
                open.append( owner )
                owners.remove( owner )
        for previous_end in previous_ends:
            try:
                dt = datetime.strptime(previous_end.end, '%I%p(next day)')
                end = dt.hour
                if now.hour < end and owner not in open:
                    open.append( owner )
                    owners.remove( owner )
            except ValueError:
                break;
    ordrs = Order.query.all( )
    orders = { }
    for o in ordrs:
        if o.business not in orders:
            orders[ o.business ] = [ ]
        orders[ o.business ].append( o )
    return render_template( 'user/businesses.html', businesses=open, orders=orders, closed = owners)



#View the menu of a certain business
@bp.route( '/menu/<int:b_id>' )
@login_required
def view_menu( b_id ):
    place = Owner.query.filter_by( id=b_id ).one_or_none( )
    items = Item.query.filter_by( owner=b_id ).all( )
    cats = Category.query.filter_by( business=b_id ).all( )

    ratings = Rating.query.filter_by( business=b_id ).all( )
    rating = None
    if ratings:
        rating = round( statistics.mean( [ r.rating for r in ratings ] ), 1 )
        print( 'Business Rating:' + str( rating ) )
    user_ratings = Rating.query.filter_by( business=b_id, user=g.user.id ).one_or_none( )
    user_rating = None
    if user_ratings:
        user_rating = user_ratings.rating

    #loop thru cat
        #for each cat, build a list of items
        #send that as orders
    #then cycle for each cat
        #for each item
            #item template
    catDict = { }
    for c in cats:
        catDict[c.name] = Item.query.filter_by( owner=b_id, category=c.id ).all( )

    #Remove all the catergories with no items
    for c in cats:
        if not catDict[c.name]:
            catDict.pop(c.name)

    #Error testing - make sure items in list as needed
    for key in catDict.keys():
        print("Category "+key)
        for item in catDict[key]:
            print("    Item: "+item.name)

    ordrs = Order.query.all( )
    orders = { }
    for o in ordrs:
        if o.business not in orders:
            orders[ o.business ] = [ ]
        orders[ o.business ].append( o )

    total_cost = sum( [ o.qty * o.item.price for o in ordrs if o.business==b_id ] )
    # discounts

    disc = Discount.query.filter_by( business=b_id ) \
            .filter( ( Discount.ttype==1 ) | ( Discount.ttype==2 ) | \
                ( ( Discount.ttype==3 ) & ( Discount.target==g.user.email ) ) ) \
            .all( )
    u_disc = UserDiscount.query.filter_by( user=g.user.id, b_id=b_id, used=False ).all( ) 
    # opening hours

    hours = Hour.query.filter_by( owner=b_id ).order_by( Hour.day ).all()
    return render_template( 'user/menu.html', business=place, menu=items, orders=orders, 
        cats=cats, catDict=catDict, user_rating=user_rating, rating=rating, disc=disc, 
        u_disc=u_disc, hours=hours, total_cost=total_cost )


@bp.route( '/addOrdr', methods=('GET', 'POST')  )
@login_required
def order_addTwo():

    if request.method == 'POST':
        b_id = request.form[ 'business' ]
        i_id = request.form[ 'item' ]
        i_qty = request.form[ 'quantity' ]

        owner = Owner.query.filter_by( id=b_id )
        item = Item.query.filter_by( id=i_id, owner=b_id )
        strn = '---adding to order with quantity of  {}'.format( i_qty )
        print(strn)
        error = ''

        if not owner.one_or_none( ):
            error = 'Invalid business id'
        elif not item.one_or_none( ):
            error = 'Invalid item id'
        else:
            order = Order( user=g.user.id, business=b_id, item_id=i_id, qty=i_qty )
            db.session.add( order )
            db.session.commit( )
            error = 'Successfully added an item to the order'

        flash( error )
        return redirect( request.referrer )


@bp.route( '/order/add/<int:b_id>/<int:i_id>' )
@login_required
def order_add( b_id, i_id):

    owner = Owner.query.filter_by( id=b_id )
    item = Item.query.filter_by( id=i_id, owner=b_id )
    print("---adding to order")
    error = ''
    if not owner.one_or_none( ):
        error = 'Invalid business id'
    elif not item.one_or_none( ):
        error = 'Invalid item id'
    else:
        order = Order( user=g.user.id, business=b_id, item_id=i_id)
        db.session.add( order )
        db.session.commit( )
        error = 'Successfully added an item to the order'

    flash( error )
    return redirect( request.referrer )

# Remove a single item from the order
@bp.route( '/order/remove/<int:o_id>' )
@login_required
def order_remove( o_id ):
    order = Order.query.filter_by( id=o_id, user=g.user.id )
    if not order.one_or_none( ):
        error = 'Invalid order id'
    else:
        order = order.one( )
        db.session.delete( order )
        db.session.commit( )
        error = 'Successfully removed an item from the order'
    flash( error )
    return redirect( request.referrer )

# Delete an entire order from a business
@bp.route( '/order/delete/<int:b_id>' )
@login_required
def order_delete( b_id ):
    order = Order.query.filter_by( user=g.user.id, business=b_id )
    if not len( order.all( ) ):
        error = 'Invalid order id'
    else:
        for o in order.all( ):
            db.session.delete( o )
        db.session.commit( )
        error = 'Successfully removed an order'
    flash( error )
    return redirect( url_for( 'user.view_menu', b_id=b_id ) )
    

@bp.route( '/order/finalise/<int:b_id>' )
@login_required
def order_finalise( b_id ):
    ordrs = Order.query.filter_by( user=g.user.id, business=b_id )
    place = Owner.query.filter_by( id=b_id ).one_or_none( )
    
    disc = UserDiscount.query.filter_by( b_id=b_id, user=g.user.id, used=False ).one_or_none( )
    cat_total = { }
    total = 0
    time = 0

    full_amt = 0
    discount_amt = 0
    error = None
    if not len( ordrs.all( ) ):
        error = 'Invalid order id'
    else:
        for o in ordrs.all( ):
            if o.item.category not in cat_total:
                cat_total[ o.item.category ] = 0
            cat_total[ o.item.category] += o.qty * o.item.price
            print( "{}: {}".format( o.item.category, cat_total[ o.item.category ] ) )
            time += o.item.time_estimate
        
        estimated = datetime.now() + timedelta(seconds=time)
        day = estimated.weekday()
        hours = Hour.query.filter_by( owner=b_id, day=day ).all( )
        previous_ends = Hour.query.filter_by( owner=b_id, day=(day-1) % 7 ).all( )
        
        open = False
        for hour in hours:
            dt1 = datetime.strptime(hour.start, '%I%p')
            hour1 = dt1.hour
            try:
                dt2 = datetime.strptime(hour.end, '%I%p')
                hour2 = dt2.hour
            except ValueError:
                dt2 = datetime.strptime(hour.end, '%I%p(next day)')
                hour2 = dt2.hour + 24
            end = 0
            for previous_end in previous_ends:
                try:
                    dt = datetime.strptime(previous_end.end, '%I%p(next day)')
                    end = dt.hour
                except ValueError:
                    continue;
            if (estimated.hour >= hour1 and estimated.hour < hour2) or (estimated.hour < end):
                open = True
                break
        if open is False:    
            error = "Your order didn't go through: The restaurant either is CLOSED or cannot complete your order in time"
            flash( error )
            return redirect( url_for( 'user.view_menu', b_id=b_id ))
            
    if disc:
        disc = disc.discount
        full_amt = sum( [ cat_total[ c ] for c in cat_total ] )
        if disc.ttype == 2:

            cat_id = Category.query.filter_by( name=disc.target ).one_or_none( )
            print( "Target is: {}".format( cat_id ) )
            if cat_id.id in cat_total:
                print( "Discounting Target: " + disc.target )
                print( cat_total )
                if disc.dtype == 0:
                    cat_total[ cat_id.id ] *= (100.0 - disc.value)/100.0
                else:
                    cat_total[ cat_id.id ] = max( 0, cat_total[ cat_id.id ] - disc.value )
            total = sum( [ cat_total[ c ] for c in cat_total ] )
        else:
            total = sum( [ cat_total[ c ] for c in cat_total ] )
            if disc.dtype == 0:
                total *= (100.0 - disc.value)/100.0
            else:
                total = max( 0, total - disc.value )
    else:
        total = sum( [ cat_total[ c ] for c in cat_total ] )

    discount_amt = -(full_amt - total)
    flash( error )
    return render_template( 'user/payment.html', total_cost=total, total_time=time, orders=ordrs.all( ), 
        business=place, discount_amt=discount_amt )

@bp.route( '/order/payment/<int:b_id>', methods=[ 'POST' ] )
@login_required
def order_payment( b_id ):
    ordrs = Order.query.filter_by( user=g.user.id, business=b_id )
    place = Owner.query.filter_by( id=b_id ).one_or_none( )

    u_disc = UserDiscount.query.filter_by( b_id=b_id, user=g.user.id, used=False ).one_or_none( )

    finalOrder = []
    total = 0
    time = 0

    comments = ''
    if request.json and 'comments' in request.json:
        comments = request.json[ 'comments' ]

    cat_total = { }

    if not len( ordrs.all( ) ):
        error = 'Invalid order id'
    else:
        for o in ordrs.all( ):
            # total = total + o.qty*o.item.price
            if o.item.category not in cat_total:
                cat_total[ o.item.category ] = 0
            cat_total[ o.item.category] += o.qty * o.item.price

            time += o.qty * o.item.time_estimate
            for _ in range( o.qty ):
                finalOrder.append( o.item.id )
        print(finalOrder)
        for o in ordrs.all( ):
            db.session.delete( o )

        if u_disc:
            disc = u_disc.discount
            if disc.ttype == 2:
                if disc.target in cat_total:
                    if disc.dtype == 0:
                        cat_total[ disc.target ] *= (100.0 - disc.value)/100.0
                    else:
                        cat_total[ disc.target ] = max( 0, cat_total[ disc.target ] - disc.value )
                    u_disc.used = True
                total = sum( [ cat_total[ c ] for c in cat_total ] )
            else:
                total = sum( [ cat_total[ c ] for c in cat_total ] )
                if disc.dtype == 0:
                    total *= (100.0 - disc.value)/100.0
                else:
                    total = max( 0, total - disc.value )
                u_disc.used = True                
        else:
            total = sum( [ cat_total[ c ] for c in cat_total ] )
        
        order_details = ','.join( str( x ) for x in finalOrder )
        digest = hashlib.md5( (g.user.name + str(datetime.now( ) ) ).encode( ) ).hexdigest( )
        order = PaidOrder( 
            user=g.user.id, 
            business=b_id, 
            order_details=order_details, 
            total=total, 
            time_estimate=time,
            time_created=datetime.now( ),
            rating=None,
            status=0,
            comments=comments,
            digest=digest[ :5 ].upper( ) )
        db.session.add( order )
        db.session.commit( )
        error = 'Successfully paid an order with price {}.'.format(total)
        print(error)
        print(finalOrder)

        note = Notification( 
                'Order ready to be made',
                business=b_id, 
                sender=g.user.id )
        db.session.add( note )
        db.session.commit( )
        
    flash( error )
    return redirect( url_for( 'user.view_menu', b_id=b_id ) )

@bp.route( '/orders' )
@login_required
def view_orders( ):
    ordrs = PaidOrder.query.filter_by( user=g.user.id ).order_by( PaidOrder.time_created.desc( ) )

    itmLst = { } # indexed by PaidOrder.id
    timeRemain = { }

    for o in ordrs:
        if o.status == 1:
            timeDiff = (datetime.now( ) - o.time_accepted).total_seconds( )
            timeDiff = min( timeDiff, o.time_estimate )
            # timeDiff = int( min( 100 * ( timeDiff / o.time_estimate ), 100 ) )
            timeRemain[ o.id ] = timeDiff

        itmLst[ o.id ] = [ ]
        for itm_id in o.order_details.split( ',' ):
            itm = Item.query.filter_by( id=int( itm_id ) ).one_or_none( )
            if itm:
                itmLst[ o.id ].append( itm.name )
    return render_template( 'user/orders.html', 
        orders=ordrs, 
        itmLst=itmLst,
        timeRemain=timeRemain )

@bp.route( '/rate/<int:b_id>/<int:user_rating>' )
@login_required
def rate( b_id, user_rating ):
    error = None
    owner = Owner.query.filter_by( id=b_id ).one_or_none( )
    if user_rating < 0 or user_rating > 5:
        error = 'User ratings must be between 0 to 5'
    elif not owner:
        flash( 'Business does not exist' )
        return redirect( url_for( 'user.home' ) )
    else:
        rating = Rating.query.filter_by( user=g.user.id, business=b_id ).one_or_none( )
        if rating:
            # modify current rating
            rating.rating = user_rating
            db.session.commit( )
        else:
            # add rating
            rating = Rating( user=g.user.id, business=b_id, rating=user_rating )
            db.session.add( rating )
            db.session.commit( )

    print( 'User_rating:' + str( user_rating ) )
    flash( error )
    return redirect( url_for( 'user.view_menu', b_id=b_id ) )

# Discounts

@bp.route( '/discounts/add', methods=[ 'POST' ] )
@login_required
def add_discount( ):
    print( "Form: " + str( request.form ) )
    b_id = request.form[ 'b_id' ]
    code = request.form[ 'code' ]
    discount = Discount.query.filter_by( code=code, business=b_id ).one_or_none( )

    error = None
    if not discount:
        error = 'Discount does not exist'
    if discount.ttype == 3 and g.user.email != discount.target:
        error = 'Discount not targeted for you'
    else:
        ud = UserDiscount.query.filter_by( b_id=b_id, user=g.user.id, used=False ).one_or_none( )
        if ud:
            error = 'Only one discount can be applied'
        else:
            g_uses = UserDiscount.query.filter_by( b_id=b_id, used=True ).all( )
            s_uses = UserDiscount.query.filter_by( b_id=b_id, user=g.user.id, used=True ).all( )

            if len( g_uses ) >= discount.uses:
                error = 'Discount has reached total usage limit and cannot be applied'
            elif len( s_uses ) >= discount.single_uses:
                error = 'Discount has reached individual usage limit and cannot be applied'
            else:
                user_dis = UserDiscount( b_id=b_id, user=g.user.id, d_id=discount.id, used=False )
                db.session.add( user_dis )
                db.session.commit( )
                error = 'Discount applied'
    flash( error )
    return redirect( request.referrer )

@bp.route( '/discounts/remove/<int:ud_id>' )
@login_required
def remove_discount( ud_id ):
    discount = UserDiscount.query.filter_by( id=ud_id ).one_or_none( )
    if discount:
        db.session.delete( discount )
        db.session.commit( )
        flash( 'Discount removed' )
    return redirect( request.referrer )

# Location Sharing
@bp.route( '/share/<int:o_id>/<float:dist>' )
@login_required
def share( o_id, dist ):
    ordr = PaidOrder.query.filter_by( id=o_id ).one_or_none( )
    if ordr:
        ordr.dist = dist
        db.session.add( ordr )
        db.session.commit( )
    return ""

# Notifications

@bp.route( '/notifications' )
@login_required
def get_notifications( ):
    note = Notification.query.filter_by( user=g.user.id ).all( )
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
    note = Notification.query.filter_by( user=g.user.id, id=n_id ).one_or_none( )
    if note:
        db.session.delete( note )
        db.session.commit( )
        return 'Notification removed successfully'
    return 'Notification not found'


@bp.route('/getNearByBuses', methods=['POST'])
@login_required
def getNearByBuses():
    longitude = request.form['longitude']
    latitude = request.form['latitude']
    print("users location : " + latitude + " and " + longitude)
    p = Pyzomato("5fcaad6c63489efcffd0208ce2adcf43")
    # Notes: for zomato api
    # categorie id 6(query string) == cafes
    # sort by real_distance(query string)
    # order by asc (query string)
    # TODO: add radius = 1500m ~ 5000m
    result = p.search(lat = latitude, lon = longitude, 
                            category = "6",
                            sort = "real_distance",
                            order = "asc")
    pp = pprint.PrettyPrinter(indent = 1)
#    pp.pprint(result)

    for bus in result['restaurants']:
        pp.pprint (bus['restaurant'])
        break

    features = []
    for bus in result['restaurants']:
        b = bus['restaurant']
        point = {
            'type' : "Point",
            'coordinates' : [b['location']['longitude'], b['location']['latitude']]
        }
        properties_ = {
            'name' : b['name'],
            'address' : b['location']['address'],
            'city' : b['location']['city']
        }
        b_ = {
            'geometry' : point,
            'type' : 'Feature',
            'properties' : properties_
        }
        features.append(b_)

    all_bus = {
        'type' : 'FeatureCollection',
        'features' : features,
    }

#    pp.pprint(all_bus)

    return jsonify(all_bus)

