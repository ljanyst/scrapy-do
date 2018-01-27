
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
`scrapyd <https://github.com/scrapy/scrapyd>`_ but written from scratch. For
the time being, it only comes with a REST API and a command line client. Version
0.3.0 will have an interactive web interface.

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

* Open another terminal window and store the server's URL in the client's
  configuration file so that you don't have to type it all the time:

  .. code-block:: console

       $ cat > ~/.scrapy-do.cfg << EOF
       > [scrapy-do]
       > url=http://localhost:7654
       > EOF


* Download the Scrapy's Quotesbot example and push the code to the server:

  .. code-block:: console

       $ git clone https://github.com/scrapy/quotesbot.git
       $ cd quotesbot
       $ scrapy-do-cl push-project
       +----------------+
       | spiders        |
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

  .. code-block:: console

       $ scrapy-do-cl list-jobs
       +--------------------------------------+-----------+--------------+-----------+-----------------------+---------+----------------------------+------------+
       | identifier                           | project   | spider       | status    | schedule              | actor   | timestamp                  | duration   |
       |--------------------------------------+-----------+--------------+-----------+-----------------------+---------+----------------------------+------------|
       | b3a61347-92ef-4095-bb68-0702270a52b8 | quotesbot | toscrape-css | RUNNING   | now                   | USER    | 2018-01-27 08:32:19.781720 |            |
       | 0a3db618-d8e1-48dc-a557-4e8d705d599c | quotesbot | toscrape-css | SCHEDULED | every 5 to 15 minutes | USER    | 2018-01-27 08:29:24.749770 |            |
       +--------------------------------------+-----------+--------------+-----------+-----------------------+---------+----------------------------+------------+
