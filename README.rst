
=========
Scrapy Do
=========

.. image:: https://api.travis-ci.org/ljanyst/scrapy-do.svg?branch=master
   :target: https://travis-ci.org/ljanyst/scrapy-do

.. image:: https://coveralls.io/repos/github/ljanyst/scrapy-do/badge.svg?branch=master
   :target: https://coveralls.io/github/ljanyst/scrapy-do?branch=master

.. image:: https://img.shields.io/pypi/v/scrapy-do.svg
   :target: https://pypi.python.org/pypi/scrapy-do
   :alt: PyPI Version


Scrapy Do is a daemon that provides a convenient way to run `Scrapy
<https://scrapy.org/>`_ spiders. It can either do it once - immediately; or it
can run them periodically, at specified time intervals. It's been inspired by
`scrapyd <https://github.com/scrapy/scrapyd>`_ but written from scratch. It
comes with a REST API, a command line client, and an interactive web interface.

 * Homepage: `https://jany.st/scrapy-do.html <https://jany.st/scrapy-do.html>`_
 * Documentation: `https://scrapy-do.readthedocs.io/en/latest/ <https://scrapy-do.readthedocs.io/en/latest/>`_

-----------
Quick Start
-----------

* Install ``scrapy-do`` using ``pip``:

  .. code-block:: console

       $ pip install scrapy-do

* Start the daemon in the foreground:

  .. code-block:: console

       $ scrapy-do -n scrapy-do

* Open another terminal window, download the Scrapy's Quotesbot example, and
  push the code to the server:

  .. code-block:: console

       $ git clone https://github.com/scrapy/quotesbot.git
       $ cd quotesbot
       $ scrapy-do-cl push-project
       +----------------+
       | quotesbot      |
       |----------------|
       | toscrape-css   |
       | toscrape-xpath |
       +----------------+

* Schedule some jobs:

  .. code-block:: console

       $ scrapy-do-cl schedule-job --project quotesbot \
           --spider toscrape-css --when 'every 5 to 15 minutes'
       +--------------------------------------+
       | identifier                           |
       |--------------------------------------|
       | 0a3db618-d8e1-48dc-a557-4e8d705d599c |
       +--------------------------------------+

       $ scrapy-do-cl schedule-job --project quotesbot --spider toscrape-css
       +--------------------------------------+
       | identifier                           |
       |--------------------------------------|
       | b3a61347-92ef-4095-bb68-0702270a52b8 |
       +--------------------------------------+

* See what's going on:

  .. figure:: https://github.com/ljanyst/scrapy-do/raw/master/docs/_static/jobs-active.png
     :scale: 50 %
     :alt: Active Jobs

     The web interface is available at http://localhost:7654 by default.

--------------------
Building from source
--------------------

Both of the steps below require `nodejs` to be installed.

* Check if things work fine:

  .. code-block:: console

       $ pip install -rrequirements-dev.txt
       $ tox

* Build the wheel:

  .. code-block:: console

       $ python setup.py bdist_wheel

---------
ChangeLog
---------

Version 0.4.0
-------------

* Migration to the Bootstrap 4 UI
* Make it possible to add a short description to jobs
* Make it possible to specify user-defined payload in each job that is passed
  on as a parameter to the python crawler
* UI updates to support the above
* New log viewers in the web UI
