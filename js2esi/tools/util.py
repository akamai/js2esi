import os
import sys
import platform
import subprocess
from contextlib import contextmanager
from js2esi import version

__author__ = "Colin Bendell"
__copyright__ = "Copyright 2017, Akamai Technologies"
__license__ = "Apache2"


@contextmanager
def chdir(dir):
    orig_dir = os.getcwd()
    os.chdir(dir)
    yield
    os.chdir(orig_dir)


def dump_system_info():
    git_describe = 'release version'
    with chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))):
        try:
            c = ['git', 'describe', '--tags', '--long']
            git_describe = subprocess.check_output(c, stderr=subprocess.STDOUT)
            last_tag, tag_dist, commit = git_describe.decode().strip().rsplit("-", 2)

            if last_tag.startswith('v'):
                # remove the 'v' prefix
                last_tag = last_tag[1:]
            if commit.startswith('g'):
                # remove the 'g' prefix added by recent git versions
                commit = commit[1:]

            # build the same version specifier as used for snapshots by rtool
            git_describe = "{version}dev{tag:04}-0x{commit}".format(
                version=last_tag,
                tag=int(tag_dist),
                commit=commit,
            )
        except:
            pass

    bin_indicator = ""  # PyInstaller builds indicator, if using precompiled binary
    if getattr(sys, 'frozen', False):
        bin_indicator = "Precompiled Binary"

    data = [
        "js2esi version: {} ({}) {}".format(version.VERSION, git_describe, bin_indicator),
        "Python version: {}".format(platform.python_version()),
        "Platform: {}".format(platform.platform()),
    ]
    d = platform.linux_distribution()
    t = "Linux distro: %s %s %s" % d
    if d[0]:  # pragma: no cover
        data.append(t)

    d = platform.mac_ver()
    t = "Mac version: %s %s %s" % d
    if d[0]:  # pragma: no cover
        data.append(t)

    d = platform.win32_ver()
    t = "Windows version: %s %s %s %s" % d
    if d[0]:  # pragma: no cover
        data.append(t)

    return "\n".join(data)
