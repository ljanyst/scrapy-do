
.. _rest-api:

========
REST API
========

This section describes the REST API provided by Scrapy Do. The responses to
all of the requests except for ``get-log`` are JSON dictionaries. Error
responses look like this:

 .. code-block:: JSON

      {
        "msg": "Error message",
        "status": "error"
      }

Successful responses have the ``status`` part set to ``ok`` and a variety of
query dependent keys described below. The request examples use `curl
<https://curl.haxx.se/>`_ and `jq <https://stedolan.github.io/jq/>`_.

---------------
``status.json``
---------------

Get information about the daemon and its environment.

* Method: ``GET``

Example request:

 .. code-block:: console

      $ curl -s "http://localhost:7654/status.json" | jq -r

 .. code-block:: JSON

      {
        "status": "ok",
        "memory-usage": 39.89453125,
        "cpu-usage": 0,
        "time": "2017-12-11 15:20:42.415793",
        "timezone": "CET; CEST",
        "hostname": "host",
        "uptime": "1d 12m 24s",
        "jobs-run": 24,
        "jobs-successful": 24,
        "jobs-failed": 0,
        "jobs-canceled": 0
      }

---------------------
``push-project.json``
---------------------

Push a project archive to the server replacing an existing one of the same
name if it is already present.

* Method: ``POST``
* Parameters:

  * ``archive`` - a binary buffer containing the project archive

  .. code-block:: console

       $ curl -s http://localhost:7654/push-project.json \
              -F archive=@quotesbot.zip | jq -r

  .. code-block:: JSON

       {
         "status": "ok",
         "name": "quotesbot",
         "spiders": [
           "toscrape-css",
           "toscrape-xpath"
         ]
       }

----------------------
``list-projects.json``
----------------------

Get a list of the projects registered with the server.

* Method: ``GET``

  .. code-block:: console

       $ curl -s http://localhost:7654/list-projects.json | jq -r

  .. code-block:: JSON

       {
         "status": "ok",
         "projects": [
           "quotesbot"
         ]
       }


---------------------
``list-spiders.json``
---------------------

List spiders provided by the given project.

* Method: ``GET``
* Parameters:

  * ``project`` - name of the project

  .. code-block:: console

       $ curl -s "http://localhost:7654/list-spiders.json?project=quotesbot" | jq -r

  .. code-block:: JSON

       {
         "status": "ok",
         "project": "quotesbot",
         "spiders": [
           "toscrape-css",
           "toscrape-xpath"
         ]
       }

---------------------
``schedule-job.json``
---------------------

Schedule a job.

* Method: ``POST``
* Parameters:

  * ``project`` - name of the project
  * ``spider`` - name of the spider
  * ``when`` - a schedling spec, see :ref:`scheduling-spec`.

  .. code-block:: console

       $ curl -s http://localhost:7654/schedule-job.json \
              -F project=quotesbot \
              -F spider=toscrape-css \
              -F "when=every 10 minutes" | jq -r

  .. code-block:: JSON

       {
         "status": "ok",
         "identifier": "5b30c8a2-42e5-4ad5-b143-4cb0420955a5"
       }

------------------
``list-jobs.json``
------------------

Get information about a job or jobs.

* Method: ``GET``
* Parameters (one required):

  * ``status`` - status of the jobs to list, see :ref:`jobs`; addtionally
    ``ACTIVE`` and ``COMPLETED`` are accepted to get lists of jobs with
    related statuses.
  * ``id`` - id of the job to list

Query by status:

  .. code-block:: console

       $ curl -s "http://localhost:7654/list-jobs.json?status=ACTIVE" | jq -r

  .. code-block:: JSON

       {
         "status": "ok",
         "jobs": [
           {
             "identifier": "5b30c8a2-42e5-4ad5-b143-4cb0420955a5",
             "status": "SCHEDULED",
             "actor": "USER",
             "schedule": "every 10 minutes",
             "project": "quotesbot",
             "spider": "toscrape-css",
             "timestamp": "2017-12-11 15:34:13.008996",
             "duration": null
           },
           {
             "identifier": "451e6083-54cd-4628-bc5d-b80e6da30e72",
             "status": "SCHEDULED",
             "actor": "USER",
             "schedule": "every minute",
             "project": "quotesbot",
             "spider": "toscrape-css",
             "timestamp": "2017-12-09 20:53:31.219428",
             "duration": null
           }
         ]
       }

Query by id:

  .. code-block:: console

       $ curl -s "http://localhost:7654/list-jobs.json?id=317d71ea-ddea-444b-bb3f-f39d82855e19" | jq -r

  .. code-block:: JSON

       {
         "status": "ok",
         "jobs": [
           {
             "identifier": "317d71ea-ddea-444b-bb3f-f39d82855e19",
             "status": "SUCCESSFUL",
             "actor": "SCHEDULER",
             "schedule": "now",
             "project": "quotesbot",
             "spider": "toscrape-css",
             "timestamp": "2017-12-11 15:40:39.621948",
             "duration": 2
           }
         ]
      }



-------------------
``cancel-job.json``
-------------------

Cancel a job.

* Method: ``POST``
* Parameters:

  * ``id`` - id of the job to cancel

  .. code-block:: console

       $ curl -s http://localhost:7654/cancel-job.json \
              -F id=451e6083-54cd-4628-bc5d-b80e6da30e72 | jq -r

  .. code-block:: JSON

       {
         "status": "ok"
       }

-----------
``get-log``
-----------

Retrieve the log file of the job that has either been completed or is still
running.

* Method:: ``GET``

Get the log of the standard output:

  .. code-block:: console

       $ curl -s http://localhost:7654/get-log/data/bf825a9e-b0c6-4c52-89f6-b5c8209e7977.out

Get the log of the standard error output:

  .. code-block:: console

       $ curl -s http://localhost:7654/get-log/data/bf825a9e-b0c6-4c52-89f6-b5c8209e7977.err

-----------------------
``remove-project.json``
-----------------------

Remove a project.

* Method: ``POST``
* Parameters:

  * ``name`` - name pf the project

  .. code-block:: console

       $ curl -s http://localhost:7654/remove-project.json \
              -F name=quotesbot | jq -r

  .. code-block:: JSON

       {
         "status": "ok"
       }
