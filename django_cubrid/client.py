import os
import sys
import django

if django.VERSION >= (1, 8):
    from django.db.backends.base.client import BaseDatabaseClient
else:
    from django.db.backends import BaseDatabaseClient


class DatabaseClient(BaseDatabaseClient):
    executable_name = 'csql'

    def runshell(self):
        settings_dict = self.connection.settings_dict
        args = [self.executable_name]
        if settings_dict['USER']:
            args += ["-u", settings_dict['USER']]
        if settings_dict['PASSWORD']:
            args += ["-p", settings_dict['PASSWORD']]
        if settings_dict['NAME'] and settings_dict['HOST']:
            args += [settings_dict['NAME'] + "@" + settings_dict['HOST']]

        if os.name == 'nt':
            sys.exit(os.system(" ".join(args)))
        else:
            os.execvp(self.executable_name, args)
