import django
if django.VERSION >= (1, 8):
    from django.db.backends.base.validation import BaseDatabaseValidation
else:
    from django.db.backends import BaseDatabaseValidation


class DatabaseValidation(BaseDatabaseValidation):
    pass
