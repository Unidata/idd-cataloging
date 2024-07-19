# IDD-Cataloging

This repo is a collection of scripts and such to help catalog the contents of the IDD.  This was thrown together pretty hastily so it won't work out of the box.  But should anyone dare go down this road again, hopefully this'll make the adventure a little easier.


# Process

The IDD-Cataloging process consists of two parts: data ingest and a front-end presentation using Flask.  

## Data Ingest

The **scripts** directory contains a data ingest script as well as a database scour script.  The general idea is to run **iddcat_ingest.py** and it will watch the IDD (using notifyme), inserting any product IDs seen into a Postgres database.  The **iddcat_scour.py** script should be run occasionally to make sure the database doesn't grow out of control or become too unwieldly to use.

## Front-End with Flask

Included here are some Flask routings and templates to showcase what's in the database.  This is not a fully configured Flask app, some assembly required.
