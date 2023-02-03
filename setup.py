#!/usr/bin/env python3
import io
import os
import sys
import shutil
import subprocess
try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command
from distutils.dir_util import remove_tree

MODULE_NAME = "binwalk"
MODULE_VERSION = "2.3.3"
SCRIPT_NAME = MODULE_NAME
MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

# Python3 has a built-in DEVNULL; for Python2, we have to open
# os.devnull to redirect subprocess stderr output to the ether.
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

# If this version of binwalk was checked out from the git repository,
# include the git commit hash as part of the version number reported
# by binwalk.
try:
    label = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=DEVNULL).decode('utf-8')
    MODULE_VERSION = "%s+%s" % (MODULE_VERSION, label.strip())
except KeyboardInterrupt:
    raise
except Exception:
    pass


def which(command):
    # /usr/local/bin is usually the default install path, though it may not be in $PATH
    usr_local_bin = os.path.sep.join([os.path.sep, 'usr', 'local', 'bin', command])

    try:
        location = subprocess.Popen(
            ["which", command],
            shell=False, stdout=subprocess.PIPE).communicate()[0].strip()
    except KeyboardInterrupt as e:
        raise e
    except Exception as e:
        pass

    if not location and os.path.exists(usr_local_bin):
        location = usr_local_bin

    return location


def find_binwalk_module_paths():
    paths = []

    try:
        import binwalk
        paths = binwalk.__path__
    except KeyboardInterrupt as e:
        raise e
    except Exception:
        pass

    return paths


def remove_binwalk_module(pydir=None, pybin=None):
    if pydir:
        module_paths = [pydir]
    else:
        module_paths = find_binwalk_module_paths()

    for path in module_paths:
        try:
            remove_tree(path)
        except OSError:
            pass

    if not pybin:
        pybin = which(MODULE_NAME)

    if pybin:
        try:
            sys.stdout.write("removing '%s'\n" % pybin)
            os.remove(pybin)
        except KeyboardInterrupt:
            pass
        except Exception:
            pass


class IDAUnInstallCommand(Command):
    description = "Uninstalls the binwalk IDA plugin module"
    user_options = [
        ('idadir=', None, 'Specify the path to your IDA install directory.'),
    ]

    def initialize_options(self):
        self.idadir = None
        self.mydir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "src")

    def finalize_options(self):
        pass

    def run(self):
        if self.idadir is None:
            sys.stderr.write(
                "Please specify the path to your IDA install directory with the '--idadir' option!\n")
            return

        binida_dst_path = os.path.join(self.idadir, 'plugins', 'binida.py')
        binwalk_dst_path = os.path.join(self.idadir, 'python', 'binwalk')

        if os.path.exists(binida_dst_path):
            sys.stdout.write("removing '%s'\n" % binida_dst_path)
            os.remove(binida_dst_path)
        if os.path.exists(binwalk_dst_path):
            sys.stdout.write("removing '%s'\n" % binwalk_dst_path)
            shutil.rmtree(binwalk_dst_path)


class IDAInstallCommand(Command):
    description = "Installs the binwalk IDA plugin module"
    user_options = [
        ('idadir=', None, 'Specify the path to your IDA install directory.'),
    ]

    def initialize_options(self):
        self.idadir = None
        self.mydir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "src")

    def finalize_options(self):
        pass

    def run(self):
        if self.idadir is None:
            sys.stderr.write(
                "Please specify the path to your IDA install directory with the '--idadir' option!\n")
            return

        binida_src_path = os.path.join(self.mydir, 'scripts', 'binida.py')
        binida_dst_path = os.path.join(self.idadir, 'plugins')

        if not os.path.exists(binida_src_path):
            sys.stderr.write(
                "ERROR: could not locate IDA plugin file '%s'!\n" %
                binida_src_path)
            return
        if not os.path.exists(binida_dst_path):
            sys.stderr.write(
                "ERROR: could not locate the IDA plugins directory '%s'! Check your --idadir option.\n" %
                binida_dst_path)
            return

        binwalk_src_path = os.path.join(self.mydir, 'binwalk')
        binwalk_dst_path = os.path.join(self.idadir, 'python')

        if not os.path.exists(binwalk_src_path):
            sys.stderr.write(
                "ERROR: could not locate binwalk source directory '%s'!\n" %
                binwalk_src_path)
            return
        if not os.path.exists(binwalk_dst_path):
            sys.stderr.write(
                "ERROR: could not locate the IDA python directory '%s'! Check your --idadir option.\n" %
                binwalk_dst_path)
            return

        binida_dst_path = os.path.join(binida_dst_path, 'binida.py')
        binwalk_dst_path = os.path.join(binwalk_dst_path, 'binwalk')

        if os.path.exists(binida_dst_path):
            os.remove(binida_dst_path)
        if os.path.exists(binwalk_dst_path):
            shutil.rmtree(binwalk_dst_path)

        sys.stdout.write("copying %s -> %s\n" %
                         (binida_src_path, binida_dst_path))
        shutil.copyfile(binida_src_path, binida_dst_path)

        sys.stdout.write("copying %s -> %s\n" %
                         (binwalk_src_path, binwalk_dst_path))
        shutil.copytree(binwalk_src_path, binwalk_dst_path)


class UninstallCommand(Command):
    description = "Uninstalls the Python module"
    user_options = [
        ('pydir=', None, 'Specify the path to the binwalk python module to be removed.'),
        ('pybin=', None, 'Specify the path to the binwalk executable to be removed.'),
    ]

    def initialize_options(self):
        self.pydir = None
        self.pybin = None

    def finalize_options(self):
        pass

    def run(self):
        remove_binwalk_module(self.pydir, self.pybin)


class CleanCommand(Command):
    description = "Clean Python build directories"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            remove_tree(os.path.join(MODULE_DIRECTORY, "build"))
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            pass

        try:
            remove_tree(os.path.join(MODULE_DIRECTORY, "dist"))
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            pass


class AutoCompleteCommand(Command):
    description = "Install bash autocomplete file"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        options = []
        autocomplete_file_path = "/etc/bash_completion.d/%s" % MODULE_NAME
        auto_complete = '''_binwalk()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="%s"

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}
complete -F _binwalk binwalk'''

        (out, err) = subprocess.Popen(["binwalk", "--help"], stdout=subprocess.PIPE).communicate()
        for line in out.splitlines():
            if b'--' in line:
                long_opt = line.split(b'--')[1].split(b'=')[0].split()[0].strip()
                options.append('--' + long_opt.decode('utf-8'))

        with open(autocomplete_file_path, "w") as fp:
            fp.write(auto_complete % ' '.join(options))

class TestCommand(Command):
    description = "Run unit-tests"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system("py.test --cov=binwalk testing")


this_directory = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Install the module, script, and support files
setup(
    name=MODULE_NAME,
    version=MODULE_VERSION,
    description="Firmware analysis tool",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Craig Heffner",
    url="https://github.com/ReFirmLabs/%s" % MODULE_NAME,
    requires=[],
    python_requires=">=3",
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    include_package_data=True,
    entry_points={
        'console_scripts': ['binwalk=binwalk.__main__:main'],
    },
    cmdclass={
        'clean': CleanCommand,
        'uninstall': UninstallCommand,
        'idainstall': IDAInstallCommand,
        'idauninstall': IDAUnInstallCommand,
        'autocomplete' : AutoCompleteCommand,
        'test': TestCommand,
    },
)
