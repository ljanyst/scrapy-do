from setuptools import setup

with open('README.rst') as readme:
    long_description = readme.read()

setup(
    name = 'scrapy-do',
    version = '0.1.0',
    author = 'Lukasz Janyst',
    author_email = 'xyz@jany.st',
    url = 'https://jany.st/scrapy-do.html',
    description = 'Spider Runner for Scrapy',
    long_description = long_description,
    license = 'BSD License',
    packages = ['scrapy_do'],
    include_package_data = True,
    package_data={
        '': ['*.conf'],
    },
    scripts=['scrapy-do'],
    classifiers = [
        'Framework :: Scrapy',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
    ],
    install_requires = [
        'scrapy', 'twisted', 'pyOpenSSL', 'psutil', 'python-dateutil',
        'schedule'
    ]
)
