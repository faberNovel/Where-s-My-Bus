Overview
========

Where's My Bus provides real-time departure times in San Francisco for the
nearest MUNI bus stops.

It uses Django, Mongodb and the [511 API](http://511.org/developer-resources_transit-api.asp).

![wheresmybus Screenshot](https://github.com/faberNovel/NextBus/raw/master/doc/images/screenshot.png)

Folder structure:

* `conf/` -> Deployment configuration files
* `doc/` -> Screenshots
* `wheresmybus/` -> Django code
* `fabfile.py` -> Fabric tasks file

Testing locally
===============

Prerequisites
-------------

Make sure you have git, MongoDB, Mercurial and 511 API tokens. Don't forget to configure
MongoDB.

Install [Pythonbrew](https://github.com/utahta/pythonbrew) and create a virtual environment:

	$ pythonbrew install 2.7.2
	$ pythonbrew switch 2.7.2
    $ pythonbrew venv create wheresmybus --no-site-packages
    $ pythonbrew venv use wheresmybus

Install fabric, django-nonrel, djangotoolbox and mongodb-engine:

	$ pip install fabric
    $ cd ~/Downloads # or another temporary folder
	$ hg clone http://bitbucket.org/wkornewald/django-nonrel && cd django-nonrel && python setup.py install && cd ..
	$ hg clone http://bitbucket.org/wkornewald/djangotoolbox && cd djangotoolbox && python setup.py install && cd ..
	$ git clone git://github.com/django-nonrel/mongodb-engine.git && cd mongodb-engine && python setup.py install && cd ..

Configuration
-------------

1. Make sure your are in the same directory as `fabfile.py` then do `fab
   setup_local`. This will install the remaining packages as well as the bus stops data.
2. Rename `wheresmybus/secrets.py.example` to `wheresmybus/secrets.py`.
3. Modify `API_TOKEN` with your 511 credentials.

You're done!

If you want to access the Django administration pages (**facultative**):

1. Get your `SITE_ID`.
2. Modify `SITE_ID` for `testing` in `wheresmybus/secrets.py`.

To get it:

	$ mongo localhost/wheresmybus
	MongoDB shell version: 1.8.3
	connecting to: localhost/wheresmybus
	> db.django_site.find()
	{ "_id" : ObjectId("4e6aa48ff6baea0e6e00001d"), "domain" : "example.com", "name" : "example.com" }

Running the local server
------------------------

    $ python manage.py runserver

Deployment
==========

This project uses Nginx, Gunicorn and Supervisor.

To create a new server:

	$ fab staging setup_server

Or:

	$ fab setup_server:hosts="host1.ec2.com"

To deploy:

	$ fab staging deploy

For more information, see `fabfile.py`.

Documentation
=============

This project uses:

* [Django](http://www.djangoproject.com/): web framework
* [Mongodb](http://www.mongodb.org/): database
* [511](http://511.org/): real-time departure times
* [SF MTA](http://www.sfmta.com/): bus stop data
* [jQuery-mobile](http://jquerymobile.com/): touch-optimized web framework for smartphones and tablets

![511 Logo](https://github.com/faberNovel/NextBus/raw/master/doc/images/511_logo.jpg)

Other interesting links:

* [SF MTA NextMuni Data](http://www.sfmta.com/cms/asite/nextmunidata.htm)
* [MongoDB Geospatial Indexing](http://www.mongodb.org/display/DOCS/Geospatial+Indexing)
* [Django MongoDB](http://django-mongodb.org/)

License
=======

MIT License - See `LICENSE.txt` for more details.

Copyright (c) 2011-2012 faberNovel

[faberNovel](http://www.fabernovel.com/) combines technology, design and
emerging trends to invent new products, services, and experiences.
