import pytest
from flask import g, session
from flaskr.models import Owner, Item, Category
from werkzeug.security import check_password_hash


"""
Account Registration
"""
def test_register( client ):
    assert client.get( '/business/register' ).status_code == 200
    response = client.post( 
        '/business/register',
        data={ 
            'b_name': 'a', 
            'email': 'a', 
            'password': 'ok',
            'long': '5',
            'lat': '6'
        }
    )
    assert response.status_code == 302

@pytest.mark.parametrize( ( 'name', 'email', 'password', 'lng', 'lat', 'message' ), (
    ( '', 'a', 'b', '151.209900', '-33.8688', b'Name is required' ),
    ( 'a', '', 'b', '151.209900', '-33.8688', b'Email is required' ),
    ( 'a', 'a', '', '151.209900', '-33.8688', b'Password is required' ),
    ( 'a', 'a', 'ok', '', '', b'Location is required' ),
    ( 'a', 'a', 'ok', '', '-33.8688', b'Location is required' ),
    ( 'a', 'a', 'ok', '151.209900', '', b'Location is required' ),
) )
def test_register_validate_input( client, name, email, password, lng, lat, message ):
    response = client.post( 
        '/business/register',
        data={ 
            'b_name': name, 
            'email': email, 
            'password': password,
            'long': lng,
            'lat': lat
        }
    )
    assert message in response.data

"""
Account Login
"""

def test_login( client ):
    response = client.post( 
        '/business/login',
        data={ 'email': 'a', 'password': 'ok' }
    )
    assert response.status_code == 302
    owner = Owner.query.filter_by( email='a' ).one( )
    with client.session_transaction() as session:
        assert 'owner_id' in session # make sure owners have owner_id in session
        assert session[ 'owner_id' ] == owner.id
    return owner.id

@pytest.mark.parametrize( ( 'email', 'password', 'message' ), (
    ( '', 'a', b'Email is required' ),
    ( 'a', '', b'Password is required' ),
    ( 'zzzz', 'a', b'Incorrect email' ),
    ( 'a', 'zzzz', b'Incorrect password' ),
) )
def test_login_validate_input( client, email, password, message ):
    response = client.post( 
        '/business/login',
        data={ 'email': email, 'password': password }
    )
    assert message in response.data


"""
Items
"""
def test_items( client ):
    b_id = test_login( client ) # we need to login to an account to add items
    default_cat = Category.query.filter_by( business=b_id, name='Other' ).one_or_none( )
    assert default_cat
    # test creating items
    response = client.post( 
        '/business/items/create',
        data={
            'name': 'Item 1',
            'desc': 'Item 1 Desc',
            'price': '1.05',
            'time': '60',
            'category': default_cat.id
        },
        follow_redirects=True
    )
    assert b'Item added successfully' in response.data
    itm = Item.query.filter_by( owner=g.owner.id, name='Item 1', desc='Item 1 Desc', price='1.05' ).one_or_none( )
    assert itm
    # test modifying the items
    response = client.post( 
        '/business/items/modify/' + str( itm.id ),
        data={
            'name': 'Item 2',
            'desc': 'Item 1 Desc',
            'price': '1.05',
            'time': '60',
            'category': default_cat.id
        },
        follow_redirects=True
    )
    assert b'Item modified successfully' in response.data
    assert itm.name == 'Item 2'
    assert itm.desc == 'Item 1 Desc'
    assert itm.price == 1.05
    assert itm.time_estimate == 60

    response = client.post( 
        '/business/items/modify/' + str( itm.id ),
        data={
            'name': 'Item 2',
            'desc': 'Item 2 Desc',
            'price': '1.05',
            'time': '60',
            'category': default_cat.id
        },
        follow_redirects=True
    )
    assert b'Item modified successfully' in response.data
    assert itm.name == 'Item 2'
    assert itm.desc == 'Item 2 Desc'
    assert itm.price == 1.05
    assert itm.time_estimate == 60

    response = client.post( 
        '/business/items/modify/' + str( itm.id ),
        data={
            'name': 'Item 2',
            'desc': 'Item 1 Desc',
            'price': '2',
            'time': '60',
            'category': default_cat.id
        },
        follow_redirects=True
    )
    assert b'Item modified successfully' in response.data
    assert itm.name == 'Item 2'
    assert itm.desc == 'Item 1 Desc'
    assert itm.price == 2
    assert itm.time_estimate == 60

    response = client.post( 
        '/business/items/modify/' + str( itm.id ),
        data={
            'name': 'Item 2',
            'desc': 'Item 1 Desc',
            'price': '2',
            'time': '1',
            'category': default_cat.id
        },
        follow_redirects=True
    )
    assert b'Item modified successfully' in response.data
    assert itm.name == 'Item 2'
    assert itm.desc == 'Item 1 Desc'
    assert itm.price == 2
    assert itm.time_estimate == 1

@pytest.mark.parametrize( ( 'name', 'desc', 'price', 'time', 'message' ), (
    ( '', 'a', '5.1', '60', b'Item Name is required' ),
    ( 'a', '', '5.1', '60', b'Description is required' ),
    ( 'a', 'a', '', '60', b'Price is required' ),
    ( 'a', 'a', '5', '', b'Estimated Time is required' ),
    ( 'a', 'a', '-1', '60', b'Invalid price' ),
    ( 'a', 'a', '50', '-1', b'Invalid time estimate' ),
    ( 'a', 'a', '1a5', '60', b'Invalid price or time estimate' ),
    ( 'a', 'a', '50', 'abc', b'Invalid price or time estimate' ),
    ( 'a', 'a', 'abc', '60', b'Invalid price or time estimate' ),
) )
def test_items_validate_input( client, name, desc, price, time, message ):
    b_id = test_login( client ) # we need to login to an account to add items
    default_cat = Category.query.filter_by( business=b_id, name='Other' ).one_or_none( )
    assert default_cat
    # test creating items
    response = client.post( 
        '/business/items/create',
        data={
            'name': name,
            'desc': desc,
            'price': price,
            'time': time,
            'category': default_cat.id
        },
        follow_redirects=True
    )
    assert message in response.data

    # test modifying items
    itm = Item.query.one_or_none( )
    assert itm
    response = client.post( 
        '/business/items/modify/' + str( itm.id ),
        data={
            'name': name,
            'desc': desc,
            'price': price,
            'time': time,
            'category': default_cat.id
        },
        follow_redirects=True
    )
    assert message in response.data

def test_items_delete( client ):
    test_login( client ) # login first
    # test deleting items
    itm = Item.query.filter_by( name='Item 2' ).one_or_none( )
    assert itm
    item_name = itm.name
    response = client.get( '/business/items/delete/' + str( itm.id ), follow_redirects=True )
    delStr = 'Item {} has been deleted'.format( item_name )
    assert str.encode( delStr ) in response.data