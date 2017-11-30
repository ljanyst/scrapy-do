#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   25.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

from configparser import ConfigParser, NoSectionError, NoOptionError
from pkgutil import get_data


#-------------------------------------------------------------------------------
class Config:
    """
    A configuration dictionary with defaults. It's a wrapper around the
    :py:class:`configparser.ConfigParser`.
    """

    #---------------------------------------------------------------------------
    def __init__(self, config_files=[], package=__package__):
        """
        Load the default configuration from the specified package

        :param config_file: A list of paths to configuration files
        :param package: Name of the package in which to search for a default
                        config file; the current package is assumed if `None`
        """
        self.conf = ConfigParser()
        default_config = get_data(package, 'default.conf').decode('utf-8')
        self.conf.read_string(default_config)
        for config_file in config_files:
            self.conf.read(config_file)

    #---------------------------------------------------------------------------
    def __get_with_type(self, getter, section, option, default):
        """
        Get a an option of a specific type.
        """
        try:
            return getter(section, option)
        except (NoSectionError, NoOptionError, ValueError):
            if default is not None:
                return default
            raise

    #---------------------------------------------------------------------------
    def get_bool(self, section, option, default=None):
        """
        Get option value and coerce to boolean.

        :raises ValueError: value can not be coerced and no default is given
        :raises NoOptionError: option is missing and no default is given
        :raises NoSectionError: section is missing and no default is given
        """
        return self.__get_with_type(self.conf.getboolean, section, option,
                                    default)

    #---------------------------------------------------------------------------
    def get_int(self, section, option, default=None):
        """
        Get option value and coerce to integer. For details see
        :meth:`get_bool <Config.get_bool>`.
        """
        return self.__get_with_type(self.conf.getint, section, option, default)

    #---------------------------------------------------------------------------
    def get_float(self, section, option, default=None):
        """
        Get option value and coerce to float. For details see
        :meth:`get_bool <Config.get_bool>`.
        """
        return self.__get_with_type(self.conf.getfloat, section, option,
                                    default)

    #---------------------------------------------------------------------------
    def get_string(self, section, option, default=None):
        """
        Get option value as string.

        :raises NoOptionError: option is missing and no default is given
        :raises NoSectionError: section is missing and no default is given
        """
        return self.__get_with_type(self.conf.get, section, option, default)

    #---------------------------------------------------------------------------
    def get_options(self, section):
        """
        Get all options in a given section
        """
        return self.conf.items(section)
