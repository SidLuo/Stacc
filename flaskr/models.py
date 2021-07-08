"""
This file contains the models of our web application which are used to
create individual tables in SQL.
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from flaskr.database import db

class User( db.Model ):
    __tablename__ = 'users'
    id = db.Column( db.Integer, primary_key=True )
    name = db.Column( db.String( 50 ) )
    email = db.Column( db.String( 120 ), unique=True )
    password = db.Column( db.Text, nullable=False )
    isguest = db.Column( db.Boolean, default=False )

    def __init__( self, name=None, email=None, password=None, isguest=False ):
        self.name = name
        self.email = email
        self.password = password
        self.isguest = isguest
    
    def __rep__( self ):
        return '<User {}>'.format( self.name )

class Owner( db.Model ):
    __tablename__ = 'owners'
    id = db.Column( db.Integer, primary_key=True )
    name = db.Column( db.String( 80 ) )
    email = db.Column( db.String( 120 ), unique=True )
    password = db.Column( db.Text, nullable=False )
    longitude = db.Column( db.Float )
    latitude = db.Column( db.Float )

    user_rating = db.Column( db.Float )
    time_rating = db.Column( db.Float )

    items = relationship( 'Item' )
    hours = relationship( 'Hour' )

    def __init__( self, name=None, email=None, password=None, lng=None, lat=None ):
        self.name = name
        self.email = email
        self.password = password
        self.longitude = lng
        self.latitude = lat
        self.user_rating = None
        self.time_rating = None

    def __rep__( self ):
        return '<Business {}>'.format( self.name )
        
class Hour( db.Model ):
    __tablename__ = 'hours'
    id = db.Column( db.Integer, primary_key=True )
    owner = db.Column( db.Integer, ForeignKey( 'owners.id' ) )
    day = db.Column( db.Integer, nullable=False )
    start = db.Column( db.String( 15 ) )
    end = db.Column( db.String( 15 ) )

class Item( db.Model ):
    __tablename__ = 'items'
    id = db.Column( db.Integer, primary_key=True )
    owner = db.Column( db.Integer, ForeignKey( 'owners.id' ) )
    name = db.Column( db.String( 80 ), nullable=False, unique=True )
    desc = db.Column( db.String( 200 ) )
    price = db.Column( db.Float, nullable=False )
    time_estimate = db.Column( db.Integer )
    visibility = db.Column( db.Boolean, default=True )
    category = db.Column( db.Integer, ForeignKey( 'category.id' ) )
    # order = relationship( 'Order', back_populates='items' )

class Order( db.Model ):
    __tablename__ = 'orders'
    id = db.Column( db.Integer, primary_key=True )
    user = db.Column( db.Integer, ForeignKey( 'users.id' ), nullable=False )
    business = db.Column( db.Integer, ForeignKey( 'owners.id' ), nullable=False )
    item_id = db.Column( db.Integer, ForeignKey( 'items.id' ), nullable=False )
    item = relationship( 'Item' )
    user_ = relationship( 'User' )
    qty = db.Column( db.Integer, nullable=False )


class PaidOrder( db.Model ):
    id = db.Column( db.Integer, primary_key=True )
    user = db.Column( db.Integer, ForeignKey( 'users.id' ), nullable=False )
    business = db.Column( db.Integer, ForeignKey( 'owners.id' ), nullable=False )
    order_details = db.Column( db.String, nullable=False )
    total = db.Column( db.Float )
    time_estimate = db.Column( db.Integer )
    status = db.Column( db.Integer )

    time_created = db.Column( db.DateTime )
    time_accepted = db.Column( db.DateTime )
    rating = db.Column( db.Float )
    dist = db.Column( db.Float )

    comments = db.Column( db.String )
    digest = db.Column( db.String( length=5 ) )

    user_ = relationship( 'User' )
    business_ = relationship( 'Owner' )

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Category( db.Model ):
    __tablename__ = 'category'
    id = db.Column( db.Integer, primary_key=True )
    business = db.Column( db.Integer, ForeignKey( 'owners.id' ), nullable=False )
    name = db.Column( db.String( 50 ), unique=True  )

class Notification( db.Model ):
    __tablename__ = 'notifications'
    id = db.Column( db.Integer, primary_key=True )

    user = db.Column( db.Integer, ForeignKey( 'users.id' ) )
    business = db.Column( db.Integer, ForeignKey( 'owners.id' ) )

    message = db.Column( db.String( ) )
    sender = db.Column( db.String( ) )
    link = db.Column( db.String( ) )

    def __init__( self, message, user=None, business=None, sender='Stacc', link='' ):
        self.user = user
        self.business = business
        self.message = message
        self.sender = sender
        self.link = link

class Rating( db.Model ):
    __tablename__ = 'ratings'
    id = db.Column( db.Integer, primary_key=True )

    user = db.Column( db.Integer, ForeignKey( 'users.id' ) )
    business = db.Column( db.Integer, ForeignKey( 'owners.id' ) )

    rating = db.Column( db.Integer )

class Discount( db.Model ):
    __tablename__ = 'discounts'
    id = db.Column( db.Integer, primary_key=True )
    
    visibility = db.Column( db.Boolean )
    code = db.Column( db.String )
    business = db.Column( db.Integer, ForeignKey( 'owners.id' ) )

    # target type
    # 0 - universal (all businesses)
    # 1 - business-wide
    # 2 - category
    # 3 - user
    ttype = db.Column( db.Integer )
    target = db.Column( db.String )

    # discount type
    # 0 - percentage
    # 1 - flat
    dtype = db.Column( db.Integer )
    value = db.Column( db.Float )

    uses = db.Column( db.Integer )
    single_uses = db.Column( db.Integer )

class UserDiscount( db.Model ):
    __tablename__ = 'userdiscounts'
    id = db.Column( db.Integer, primary_key=True )

    b_id = db.Column( db.Integer, ForeignKey( 'owners.id' ) )
    user = db.Column( db.Integer, ForeignKey( 'users.id' ) )
    d_id = db.Column( db.Integer, ForeignKey( 'discounts.id' ) )
    discount = relationship( 'Discount' )

    used = db.Column( db.Boolean )