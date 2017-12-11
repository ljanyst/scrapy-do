===========
Quick Start
===========

* Install ``scrapy-do`` using ``pip``:

  .. code-block:: console

       $ pip install scrapy-do

* Start the daemon in the foreground:

  .. code-block:: console

       $ scrapy-do -n scrapy-do

* Open another terminal window, download the Scrapy's Quotesbot example and
  create a deployable archive:

  .. code-block:: console

       $ git clone https://github.com/scrapy/quotesbot.git
       $ cd quotesbot
       $ git archive master -o quotesbot.zip --prefix=quotesbot/

* Push the code to the server:

  .. code-block:: console

       $ curl -s http://localhost:7654/push-project.json \
              -F name=quotesbot \
              -F archive=@quotesbot.zip | jq -r
       {
         "status": "ok",
         "spiders": [
           "toscrape-css",
           "toscrape-xpath"
         ]
       }

* Schedule some jobs:

  .. code-block:: console

       $ curl -s http://localhost:7654/schedule-job.json \
              -F project=quotesbot \
              -F spider=toscrape-css \
              -F "when=every 2 to 3 hours" | jq -r
       {
         "status": "ok",
         "identifier": "04a38a03-1ce4-4077-aee1-e8275d1c20b6"
       }

       $ curl -s http://localhost:7654/schedule-job.json \
              -F project=quotesbot \
              -F spider=toscrape-css \
              -F when=now | jq -r
       {
         "status": "ok",
         "identifier": "83d447b0-ba6e-42c5-a80f-6982b2e860cf"
       }

* See what's going on:

  .. code-block:: console

       $ curl -s "http://localhost:7654/list-jobs.json?status=ACTIVE" | jq -r
       {
         "status": "ok",
         "jobs": [
           {
             "identifier": "83d447b0-ba6e-42c5-a80f-6982b2e860cf",
             "status": "RUNNING",
             "actor": "USER",
             "schedule": "now",
             "project": "quotesbot",
             "spider": "toscrape-css",
             "timestamp": "2017-12-10 22:33:14.853565",
             "duration": null
           },
           {
             "identifier": "04a38a03-1ce4-4077-aee1-e8275d1c20b6",
             "status": "SCHEDULED",
             "actor": "USER",
             "schedule": "every 2 to 3 hours",
             "project": "quotesbot",
             "spider": "toscrape-css",
             "timestamp": "2017-12-10 22:31:12.320832",
             "duration": null
           }
         ]
       }
