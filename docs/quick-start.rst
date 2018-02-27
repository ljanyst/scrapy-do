===========
Quick Start
===========

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

  .. figure:: _static/jobs-active.png
     :scale: 50 %
     :alt: Active Jobs

     The web interface is available at http://localhost:7654 by default.

