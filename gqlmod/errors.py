import collections.abc


class MissingProviderError(SyntaxError):
    """
    No provider given.
    """

    def __init__(self, filename):
        super().__init__()
        self.msg = self.__doc__
        self.filename = filename
        self.lineno = 1
        self.print_file_and_line = False


class MultiErrors(collections.abc.Sequence, Exception):
    def __init__(self, errors):
        super().__init__()
        self._errors = list(errors)
        self.msg = "Multiple Errors:\n" + '\n'.join(map(str, errors))

    def __len__(self):
        return len(self._errors)

    def __getitem__(self, index):
        return self._errors[index]


def from_graphql_validate(error_list):
    """
    Generate a Python exception from a list of graphql.error.GraphQLError.
    """
    assert len(error_list) > 0
    if len(error_list) == 1:
        return error_list[0]
    else:
        return MultiErrors(error_list)
