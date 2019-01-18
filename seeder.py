import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Company, Base, Phone, User

engine = create_engine('sqlite:///phonemakers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create admin user
User1 = User(name="admin", email="admin@email.com")
session.add(User1)
session.commit()

samsung = Company(name="Samsung")

session.add(samsung)
session.commit()

phone = Phone(
    name="Samsung Galaxy S 2", modelNo="I9100", price="$70.50",
    launchYear=datetime.datetime.strptime('2001/01/01', '%Y/%m/%d').date(),
    company=samsung, user=User1)

session.add(phone)
session.commit()

phone = Phone(
    name="Samsung Galaxy Note 9", modelNo="SM-N96U", price="$250.00",
    launchYear=datetime.datetime.strptime('2018/01/01', '%Y/%m/%d').date(),
    company=samsung)

session.add(phone)
session.commit()

phone = Phone(
    name="Samsung Galaxy S7 edge", modelNo="G935F", price="$150.00",
    launchYear=datetime.datetime.strptime('2016/02/01', '%Y/%m/%d').date(),
    company=samsung)

session.add(phone)
session.commit()

motorola = Company(name="Motorola")

session.add(motorola)
session.commit()

phone = Phone(
    name="Motorola DROID RAZR", modelNo="XT912", price="$60.50",
    launchYear=datetime.datetime.strptime('2011/01/01', '%Y/%m/%d').date(),
    company=motorola)

session.add(phone)
session.commit()

phone = Phone(
    name="Motorola Moto X Force", modelNo="XT1058", price="$50.00",
    launchYear=datetime.datetime.strptime('2012/11/01', '%Y/%m/%d').date(),
    company=motorola)

session.add(phone)
session.commit()

phone = Phone(
    name="Motorola Moto Z3", modelNo="XT1929", price="$400.00",
    launchYear=datetime.datetime.strptime('2018/9/01', '%Y/%m/%d').date(),
    company=motorola)

session.add(phone)
session.commit()

apple = Company(name="Apple")

session.add(motorola)
session.commit()

phone = Phone(
    name="Apple iPhone XS Max", modelNo="A2102", price="$1,477.00",
    launchYear=datetime.datetime.strptime('2018/11/19', '%Y/%m/%d').date(),
    company=apple)

session.add(phone)
session.commit()

phone = Phone(
    name="Apple iPhone 8 plus", modelNo="A1863", price="$700.00",
    launchYear=datetime.datetime.strptime('2017/11/07', '%Y/%m/%d').date(),
    company=apple)
session.add(phone)
session.commit()

phone = Phone(
    name="Apple iPhone XR", modelNo="A2106", price="$459.00",
    launchYear=datetime.datetime.strptime('2018/10/01', '%Y/%m/%d').date(),
    company=apple)

session.add(phone)
session.commit()

print "added!"
