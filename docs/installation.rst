============
Installation
============

------------
The easy way
------------

The easiest way to install Scrapy Do is using ``pip``. You can then create a
directory where you want your project data stored and just start the daemon
there.

  .. code-block:: console

       $ pip install scrapy-do
       $ mkdir /home/user/my-scrapy-do-data
       $ cd /home/user/my-scrapy-do-data
       $ scrapy-do scrapy-do

Yup, you need to type ``scrapy-do`` twice. That's how `twisted
<http://twistedmatrix.com/trac/>`_ works, don't ask me. After doing that, you
will see some content in this directory including the log file and the pidfile
of the Scrapy Do daemon.

-----------------
A systemd service
-----------------

Installing Scrapy Do as a
`systemd <https://freedesktop.org/wiki/Software/systemd/>`_ service is a far
better idea than the easy way described above. It's a bit of work that should
really be done by a proper Debian/Ubuntu package, but we do not have one for
the time being, so I will show you how to do it "by hand."

* Although not strictly necessary, it's a good practice to run the daemon under
  a separate user account. I will create one called ``pydaemon`` because I run
  a couple more python daemons this way.

  .. code-block:: console

       $ sudo useradd -m -d /opt/pydaemon pydaemon

* Make sure you have all of the following packages installed:

  .. code-block:: console

       $ sudo apt-get install python3 python3-dev python3-virtualenv
       $ sudo apt-get install build-essential

* Switch your session to this new user account:

  .. code-block:: console

       $ sudo su - pydaemon

* Create the virtual env and install Scrapy Do:

  .. code-block:: console

       $ mkdir virtualenv
       $ cd virtualenv/
       $ python3 /usr/lib/python3/dist-packages/virtualenv.py -p /usr/bin/python3 .
       $ . ./bin/activate
       $ pip install scrapy-do
       $ cd ..

* Create a bin directory and a wrapper script that will set up the virtualenv on
  startup:

  .. code-block:: console

       $ mkdir bin
       $ cat > bin/scrapy-do << EOF
       > #!/bin/bash
       > . /opt/pydaemon/virtualenv/bin/activate
       > exec /opt/pydaemon/virtualenv/bin/scrapy-do "\${@}"
       > EOF
       $ chmod 755 bin/scrapy-do

* Create a data directory and a configuration file:

  .. code-block:: console

       $ mkdir -p data/scrapy-do
       $ mkdir etc
       $ cat > etc/scrapy-do.conf << EOF
       > [scrapy-do]
       > project-store = /opt/pydaemon/data/scrapy-do
       > EOF

* As root, create the following file with the following content:

  .. code-block:: console

       # cat > /etc/systemd/system/scrapy-do.service << EOF
       > [Unit]
       > Description=Scrapy Do Service
       >
       > [Service]
       > ExecStart=/opt/pydaemon/bin/scrapy-do --nodaemon --pidfile= \
       >           scrapy-do --config /opt/pydaemon/etc/scrapy-do.conf
       > User=pydaemon
       > Group=pydaemon
       > Restart=always
       >
       > [Install]
       > WantedBy=multi-user.target
       > EOF

* You can then reload the systemd configuration and let it manage the Scrapy Do
  daemon:

  .. code-block:: console

       $ sudo systemctl daemon-reload
       $ sudo systemctl start scrapy-do
       $ sudo systemctl enable scrapy-do

* Finally, you should now be able to see that the daemon is running:

  .. code-block:: console

       $ sudo systemctl status scrapy-do
       ● scrapy-do.service - Scrapy Do Service
          Loaded: loaded (/etc/systemd/system/scrapy-do.service; enabled; vendor preset: enabled)
          Active: active (running) since Sun 2017-12-10 22:42:55 UTC; 4min 23s ago
        Main PID: 27543 (scrapy-do)
       ...

I know its awfully complicated. I will do some packaging work when I have a
spare moment.
