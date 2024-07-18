#!/home/ldm/.conda/envs/iddcat/bin/python

from datetime import datetime as dt
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base

# Number of days to retain DB entries for:
KEEP_DAYS = 21


# create a SQLAlchemy engine object that connects to your PostgreSQL database
engine = create_engine('postgresql://username:password@localhost/iddcat')
Base = automap_base()
Base.prepare(autoload_with=engine)

# Get our tables:
Products = Base.classes.products

# Create session:
Session = sessionmaker(bind=engine)
session = Session()

# Scour old products:
cutoff = dt.now() - timedelta(days=KEEP_DAYS)
prod_list = session.query(Products).filter(Products.insertion_dt <= cutoff)
num_prods = prod_list.count()
prod_list.delete(synchronize_session=False)
session.commit()
session.close()

print(f"{num_prods} products have been removed from the database.")
print("Have a nice day!")
