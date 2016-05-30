import os


def get_path(relative_path=None):
    """ Return an absolute path to a project relative path. """

    path_components = [os.path.dirname(__file__), "..", ".."]
    root_path = os.path.abspath(os.path.join(*path_components))

    if relative_path is None:
        return root_path
    else:
        return os.path.abspath(os.path.join(root_path, relative_path))
