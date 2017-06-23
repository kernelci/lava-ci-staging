#!/usr/bin/python
#
# Copyright (C) 2015 Linaro Limited
# Copyright (C) 2016 Baylibre SAS
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import os
import ConfigParser
import keyring.core

class Configuration(object):
    def __init__(self, config_sources=None):
        self.config_sources = config_sources or list()


    def add_config_override(self, config_source):
        self.config_sources.insert(0, config_source)


    def get(self, variable_name):
        for config_source in self.config_sources:
            var = config_source.get(variable_name)
            if var:
                #print 'Found variable "%s" in source %s' % (variable_name,
                #        config_source.__class__.__name__)
                return var


    def add_token_from_keyring(self):
        server = self.get('server')
        username = self.get('username')
        if server and username:
            token = keyring.core.get_password("lava-tool-%s" % server, username)
            self.add_config_override(ArgumentParser({'token': token}))


class EnvConfigParser(object):
    def __init__(self):
        self.variables = dict()
        self.trans = {
                "username": "LAVA_USER",
                "server": "LAVA_SERVER",
                "token": "LAVA_TOKEN",
                "jobs": "LAVA_JOBS"
                }


    def get(self, variable):
        if not variable in self.trans:
            return None

        if variable in self.variables: return self.variables.get(variable)

        trans_var = self.trans.get(variable)
        resp = os.environ.get(trans_var, None)
        self.variables[variable] = resp
        return resp



class FileConfigParser(object):
    def __init__(self, filename=None, section=None):
        self.section = section
        self.filename = filename or os.path.expanduser('~/.lavarc')

        self.config_parser = ConfigParser.ConfigParser()

        self.config_parser.readfp(open(self.filename))

        self.variables = dict()


    def get(self, variable):
        if variable in self.variables:
            return self.variables.get(variable)

        if self.config_parser:
            if self.config_parser.has_option(self.section, variable):
                resp = self.config_parser.get(self.section, variable)
                self.variables[variable] = resp
                return resp

        return None


class ArgumentParser(object):
    def __init__(self, args):
        self.args = args

    def get(self, variable):
        return self.args.get(variable)


def get_config(args):
    config = Configuration()
    try:
        config.add_config_override(FileConfigParser(filename=args.get('config', None), section=args.get('section', None)))
        config.add_config_override(EnvConfigParser())
    except IOError:
        pass
    config.add_config_override(ArgumentParser(args))

    if not config.get('token'):
        config.add_token_from_keyring()

    return config


# vim: set ts=8 sw=4 sts=4 et tw=80 fileencoding=utf-8 :
