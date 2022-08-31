import filetype
import mimetypes
import os
import shutil
import subprocess
import tarfile
from collections import defaultdict
from itertools import groupby
from operator import itemgetter


def get_mime_type(filepath):
    mime_type = mimetypes.MimeTypes().guess_type(filepath)[0]
    if not mime_type:
        try:
            mime_type = filetype.guess_mime(filepath)
        except TypeError:
            pass
    return mime_type


def create_dir(directory):
    """
    Create a directory to store non source RPMs files.
    """
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory, ignore_errors=True)
        os.makedirs(directory)
    except Exception as err:
        raise RuntimeError(err) from None
    return directory


def uncompress_source_tarball(src_file, dest_dir=None):
    """
    Uncompress source tarball to destination directory,
    and remove the source tarball.
    """
    try:
        t = tarfile.open(src_file)
        dest_dir = os.path.dirname(src_file) if not dest_dir else dest_dir
        t.extractall(path=dest_dir)
    except Exception as err:
        err_msg = f"Failed to uncompress source tarball: {err}."
        raise ValueError(err_msg) from None
    else:
        os.remove(src_file)


def group_components(components, key='type'):
    """ # noqa
    Group by the remote source components.
    Example:
    [
        {'name': 'github.com/blang/semver', 'type': "go-package", 'version': 'v3.5.1+incompatible', ...},
        {'name': 'github.com/hashicorp/go-syslog', 'type': "gomod", 'version': 'v1.0.0', ...},
        {'name': 'encoding/csv', 'type': "go-package", 'version': '', ...},
        {'name': 'tunnel-agent', 'type': "yarn", 'version': '0.6.0', ...},
        {'name': 'github.com/mattn/go-isatty', 'type': "gomod", 'version': 'v0.0.12', ...},
        {'name': 'umd', 'type': "yarn", 'version': '3.0.3', ...},
    ]
    Result:
    {
        'go-package': [
            {'name': 'github.com/blang/semver', 'type': 'go-package', 'version': 'v3.5.1+incompatible', ...},
            {'name': 'encoding/csv', 'type': 'go-package', 'version': '', ...}
        ],
        'gomod': [
            {'name': 'github.com/hashicorp/go-syslog', 'type': 'gomod', 'version': 'v1.0.0', ...},
            {'name': 'github.com/mattn/go-isatty', 'type': 'gomod', 'version': 'v0.0.12', ...}
        ],
        'yarn': [
            {'name': 'tunnel-agent', 'type': 'yarn', 'version': '0.6.0', ...},
            {'name': 'umd', 'type': 'yarn', 'version': '3.0.3', ...}
        ]
    }
    """
    result = defaultdict(list)
    for key, items in groupby(components, key=itemgetter(key)):
        for i in items:
            result[key].append(i)
    return dict(result)


def compress_source_to_tarball(dest_file, src_dir):
    """
    Compress source in the directory to tar.gz file,
    and remove the source directory.
    """
    try:
        # Using this command to make sure source tarball same
        # checksum if compress same source.
        cmd = "tar -c  * | gzip -n > %s" % dest_file
        subprocess.check_call(cmd, shell=True, cwd=src_dir)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e) from None
    else:
        shutil.rmtree(src_dir)


def get_nvr_list_from_components(components, comp_type):
    nvr_list = []
    for component in components.get(comp_type):
        nvr = "{name}-{version}-{release}".format(**component)
        nvr_list.append(nvr)
    return nvr_list
