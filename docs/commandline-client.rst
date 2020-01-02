
===================
Command Line Client
===================

The command line client is a thin wrapper over the :ref:`rest-api`. Its purpose
is to make the command invocations more succinct and to format the responses.
The command name is ``scrapy-do-cl``. It is followed by a bunch of optional
global parameters, the name of the command to be executed, and the command's
parameters:

``scrapy-do-cl [global parameters] command [command parameters]``

--------------------------------------------
Global parameters and the configuration file
--------------------------------------------

* ``--url`` - the URL of the ``scrapy-do`` server, i.e.:
  ``http://localhost:7654``

* ``--username`` - user name, in case the server is configured to perform
  authentication

* ``--password`` - user password; if the password is not specified and was not
  configured in the configuration file, the user will be prompted to type
  it in the terminal.

* ``--print-format`` - the format of the output; valid options are ``simple``,
  ``grid``, ``fancy_grid``, ``presto``, ``psql``, ``pipe``, ``orgtbl``,
  ``jira``, ``rst``, ``mediawiki``, ``html``, ``latex``; defaults to ``psql``.

* ``--verify-ssl`` - a boolean determining whether the SSL certificate checking
  should be enabled; defaults to ``True``

The defaults for some of these parameters may be specified in the ``scrapy-do``
section of the ``~/.scrapy-do.cfg`` file. The parameters configurable this way
are: ``url``, ``username``, ``password``, and ``print-format``.

-----------------------------
Commands and their parameters
-----------------------------

status
------

Get information about the daemon and its environment.

Example:

 .. code-block:: console

      $ scrapy-do-cl status
      +-----------------+----------------------------+
      | key             | value                      |
      |-----------------+----------------------------|
      | cpu-usage       | 0.0                        |
      | memory-usage    | 42.9765625                 |
      | jobs-canceled   | 0                          |
      | timezone        | UTC; UTC                   |
      | uptime          | 1m 12d 8h 44m 58s          |
      | jobs-run        | 761                        |
      | status          | ok                         |
      | jobs-failed     | 0                          |
      | hostname        | ip-172-31-35-215           |
      | time            | 2018-01-27 08:28:55.625109 |
      | jobs-successful | 761                        |
      +-----------------+----------------------------+

push-project
------------

Push a project archive to the server replacing an existing one of the same
name if it is already present.

Parameters:

* ``--project-path`` - path to the project that you intend to push; defaults to
  the current working directory


Example:

 .. code-block:: console

       $ scrapy-do-cl push-project
       +----------------+
       | quotesbot      |
       |----------------|
       | toscrape-css   |
       | toscrape-xpath |
       +----------------+


list-projects
-------------

Get a list of the projects registered with the server.

Example:

 .. code-block:: console

      $ scrapy-do-cl list-projects
      +-----------+
      | name      |
      |-----------|
      | quotesbot |
      +-----------+


list-spiders
------------

List spiders provided by the given project.

Parameters:

* ``--project`` - name of the project

Example:

 .. code-block:: console

      $ scrapy-do-cl list-spiders --project quotesbot
      +----------------+
      | name           |
      |----------------|
      | toscrape-css   |
      | toscrape-xpath |
      +----------------+

schedule-job
------------

Schedule a job.

Parameters:

  * ``--project`` - name of the project
  * ``--spider`` - name of the spider
  * ``--when`` - a schedling spec, see :ref:`scheduling-spec`; defaults to
    ``now``
  * ``--description`` - a short description of the job instance; defaults to
    an empty string
  * ``--payload`` - a valid JSON object for user-specified payload that will be
    passed as an argument to the spider code; defaults to ``{}``

Example:

 .. code-block:: console

        $ scrapy-do-cl schedule-job --project quotesbot \
            --spider toscrape-css --when 'every 10 minutes' \
            --payload '{"test": [1, 2, 3]}'
        +--------------------------------------+
        | identifier                           |
        |--------------------------------------|
        | 2abf7ff5-f5fe-47d2-96cd-750f8701aa27 |
        +--------------------------------------+

list-jobs
---------

Get information about a job or jobs.

Parameters:

  * ``--status`` - status of the jobs to list, see :ref:`jobs`; addtionally
    ``ACTIVE`` and ``COMPLETED`` are accepted to get lists of jobs with
    related statuses; defaults to ``ACTIVE``
  * ``--job-id`` - id of the job to list; superceeds ``--status``

Query by status:

  .. code-block:: console

       $ scrapy-do-cl list-jobs --status SCHEDULED
       +--------------------------------------+-----------+----------------+-----------+-----------------------+---------------+---------+----------------------------+------------+---------------------+
       | identifier                           | project   | spider         | status    | schedule              | description   | actor   | timestamp                  | duration   | payload             |
       |--------------------------------------+-----------+----------------+-----------+-----------------------+---------------+---------+----------------------------+------------+---------------------|
       | fd2394db-70df-4343-8d1a-88f74cd64862 | quotesbot | toscrape-xpath | SCHEDULED | every 10 minutes      |               | USER    | 2020-01-02 22:59:13.423388 |            | {"test": [1, 2, 3]} |
       | 3b97239e-b9bb-474a-8b97-f1d17222f068 | quotesbot | toscrape-css   | SCHEDULED | every 5 to 15 minutes | test #1       | USER    | 2020-01-02 22:54:10.886312 |            | {"test": 1}         |
       +--------------------------------------+-----------+----------------+-----------+-----------------------+---------------+---------+----------------------------+------------+---------------------+

Query by id:

  .. code-block:: console

       $ scrapy-do-cl list-jobs --job-id fd2394db-70df-4343-8d1a-88f74cd64862
       +--------------------------------------+-----------+----------------+-----------+------------------+---------------+---------+----------------------------+------------+---------------------+
       | identifier                           | project   | spider         | status    | schedule         | description   | actor   | timestamp                  | duration   | payload             |
       |--------------------------------------+-----------+----------------+-----------+------------------+---------------+---------+----------------------------+------------+---------------------|
       | fd2394db-70df-4343-8d1a-88f74cd64862 | quotesbot | toscrape-xpath | SCHEDULED | every 10 minutes |               | USER    | 2020-01-02 22:59:13.423388 |            | {"test": [1, 2, 3]} |
       +--------------------------------------+-----------+----------------+-----------+------------------+---------------+---------+----------------------------+------------+---------------------+

cancel-lob
----------

Cancel a job.

Parameters:

  * ``--job-id`` - id of the job to cancel

Example:

  .. code-block:: console

       $ scrapy-do-cl cancel-job --job-id 2abf7ff5-f5fe-47d2-96cd-750f8701aa27
       Canceled.

get-log
-------

Retrieve the log file of the job that has either been completed or is still
running.

Parameters:

  * ``--job-id`` - id of the job
  * ``--log-type`` - ``out`` for standard output; ``err`` for standard error
    output

Example:

  .. code-block:: console

       $ scrapy-do-cl get-log --job-id b37be5b0-24bc-4c3c-bfa8-3c8e305fd9a3 \
           --log-type err

remove-project
--------------

Remove a project.

Parameters:

  * ``name`` - name of the project

  .. code-block:: console

        $ scrapy-do-cl remove-project --project quotesbot
        Removed.
