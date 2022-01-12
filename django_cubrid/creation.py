import sys
import os
import time
import subprocess
import django

from django.db.backends.base.creation import BaseDatabaseCreation

# The prefix to put on the default database name when creating
# the test database.
TEST_DATABASE_PREFIX = 'test_'


class DatabaseCreation(BaseDatabaseCreation):
    def sql_for_inline_foreign_key_references(self, field, known_models, style):
        "Return the SQL snippet defining the foreign key reference for a field"
        qn = self.connection.ops.quote_name
        rel_to = field.rel.to
        if rel_to in known_models or rel_to == model:
            output = [style.SQL_KEYWORD('FOREIGN KEY') + ' ' + \
                style.SQL_KEYWORD('REFERENCES') + ' ' + \
                style.SQL_TABLE(qn(field.rel.to._meta.db_table)) + ' (' + \
                style.SQL_FIELD(qn(field.rel.to._meta.get_field(field.rel.field_name).column)) + ')' +
                self.connection.ops.deferrable_sql()
            ]
            pending = False
        else:
            # We haven't yet created the table to which this field
            # is related, so save it for later.
            output = []
            pending = True

        return output, pending

    def sql_indexes_for_model(self, model, style):
        """
        Returns the CREATE INDEX SQL statements for a single model.
        The reference coloum can't be indexed in CUBRID.
        """
        if not model._meta.managed or model._meta.proxy:
            return []
        output = []
        for f in model._meta.local_fields:
            if not f.rel:
                output.extend(self.sql_indexes_for_field(model, f, style))

        for fs in model._meta.index_together:
            fields = [model._meta.get_field_by_name(f)[0] for f in fs]
            output.extend(self.sql_indexes_for_fields(model, fields, style))
        return output

    def _create_test_db(self, verbosity, autoclobber, keepdb=False):
        "Internal implementation - creates the test db tables."
        suffix = self.sql_table_creation_suffix()

        if 'TEST_NAME' in self.connection.settings_dict:
            test_database_name = self.connection.settings_dict['TEST_NAME']
        else:
            test_database_name = TEST_DATABASE_PREFIX + self.connection.settings_dict['NAME']

        qn = self.connection.ops.quote_name

        # Create the test database and start the cubrid server.
        check_command = ["cubrid", "checkdb", test_database_name]
        create_command = ["cubrid", "createdb" , "--db-volume-size=20M", "--log-volume-size=20M",
                          "--log-page-size=4K", "--db-page-size=4K",test_database_name, "en_US.utf8"]
        start_command = ["cubrid", "server", "start", test_database_name]
        stop_command = ["cubrid", "server", "stop", test_database_name]
        delete_command = ["cubrid", "deletedb", test_database_name]

        if keepdb:
            # Check if the test database already exists, in case keepdb is True
            try:
                subprocess.run(check_command, check = True)
                print("Database already exists")
                return # nothing to do if tit already exists
            except subprocess.CalledProcessError:
                pass # go ahead and create it

        try:
            server_version = self.connection.get_server_version().split(".")
            # server_version = ["9", "x", "x", "x"]
            if int (server_version[0]) <= 8: #8.x version
                # locale argument in the createdb command must be removed.
                create_command.pop(-1)
        except:
            pass

        try:
            cp = subprocess.run(create_command, capture_output = True)
            sys.stdout.write(cp.stdout.decode())
            sys.stderr.write(cp.stderr.decode())
            cp.check_returncode()
            print('Created')
            subprocess.run(start_command, check = True)
            print('Started')
            subprocess.run(check_command, check = True)
            cursor = self.connection.cursor()

        except Exception as e:
            sys.stderr.write("Got an error creating the test database: %s\n" % e)
            if not autoclobber:
                confirm = input("Type 'yes' if you would like to try deleting the test database '%s', or 'no' to cancel: " % test_database_name)
            if autoclobber or confirm == 'yes':
                try:
                    if verbosity >= 1:
                        print("Destroying old test database...")
                        subprocess.run(stop_command)
                        subprocess.run(delete_command)

                        print("Creating test database...")
                        cp = subprocess.run(create_command, capture_output = True)
                        sys.stdout.write(cp.stdout.decode())
                        sys.stderr.write(cp.stderr.decode())
                        cp.check_returncode()
                        print('Created')

                        subprocess.run(start_command)
                except Exception as e:
                    sys.stderr.write("Got an error recreating the test database: %s\n" % e)
                    sys.exit(2)
            else:
                print( "Tests cancelled.")
                sys.exit(1)

        return test_database_name

    def _rollback_works(self):
        cursor = self.connection.cursor()
        cursor.execute('CREATE TABLE ROLLBACK_TEST (X INT)')
        self.connection._commit()
        cursor.execute('INSERT INTO ROLLBACK_TEST (X) VALUES (8)')
        self.connection._rollback()
        cursor.execute('SELECT COUNT(X) FROM ROLLBACK_TEST')
        count, = cursor.fetchone()
        cursor.execute('DROP TABLE ROLLBACK_TEST')
        self.connection._commit()
        return count == 0

    def _destroy_test_db(self, test_database_name, verbosity):
        "Internal implementation - remove the test db tables."
        # Remove the test database to clean up after
        # ourselves. Connect to the previous database (not the test database)
        # to do so, because it's not allowed to delete a database while being
        # connected to it.
        cursor = self.connection.cursor()

        time.sleep(1) # To avoid "database is being accessed by other users" errors.
        subprocess.run(["cubrid", "server", "stop", test_database_name])
        subprocess.run(["cubrid", "deletedb", test_database_name])

        self.connection.close()
