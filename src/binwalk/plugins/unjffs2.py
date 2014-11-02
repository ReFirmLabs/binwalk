import os
import sys
import subprocess
import binwalk.core.common
import binwalk.core.compat
import binwalk.core.plugin

class JFFS2Exception(Exception):
    pass

class JFFS2Entry(object):

    def __init__(self, **kwargs):
        for (k, v) in binwalk.core.compat.iterator(kwargs):
            setattr(self, k, v)

class UnJFFS2(object):
    '''
    User space JFFS2 extractor; just a simple Python wrapper around the jffs2dump
    and jffs2reader utilities from mtd-utils. Not terribly efficient, but works.
    '''
    def __init__(self, image, directory, verbose=False):
        self.image = image
        self.verbose = verbose
        self.directory = directory

        if not os.path.exists(self.image):
            raise JFFS2Exception("Invalid/non-existant image: '%s'" % self.image)

        try:
            os.mkdir(self.directory)
        except OSError as e:
            raise JFFS2Exception("Failed to create output directory '%s': %s" % (self.directory, str(e)))

    def parse_permission(self, perm_txt):
        perm = 0

        for i in range(0, 3):
            if perm_txt[::-1][i] != '-':
                perm |= (1 << i)

        return perm

    def parse_permissions(self, permissions):
        ftype = permissions[0]
        owner = self.parse_permission(permissions[1:4])
        group = self.parse_permission(permissions[4:7])
        other = self.parse_permission(permissions[7:10])
        perms = (owner * 64) + (group * 8) + other

        return (ftype, perms)

    def ls(self):
        entries = []

        # jffs2reader self.image -d / -r
        (stdout, stderr) = subprocess.Popen(['jffs2reader', self.image, '-d', '/', '-r'], stdout=subprocess.PIPE).communicate()

        # Handle big endian images
        if not stdout and not stderr:
            subprocess.call(['jffs2dump', '-b', '-e', self.image + '.le', self.image])
            self.image += '.le'

            # jffs2reader self.image -d / -r
            (stdout, stderr) = subprocess.Popen(['jffs2reader', self.image, '-d', '/', '-r'], stdout=subprocess.PIPE).communicate()

        for line in binwalk.core.compat.bytes2str(stdout).splitlines():
            parts = [x for x in line.split(' ') if x]
            parts = parts[:5] + [' '.join(parts[5:])]

            uid = int(parts[2])
            guid = int(parts[3])

            fpath = parts[-1]
            symlink = ""

            (ftype, permissions) = self.parse_permissions(parts[0])

            if ftype == 'l' and '->' in fpath:
                (fpath, symlink) = fpath.split('->', 1)
                fpath = fpath.strip()
                symlink = symlink.strip()

            if fpath.startswith(os.path.sep):
                fpath = fpath[1:]
            if symlink and symlink.startswith(os.path.sep):
                symlink = symlink[1:]

            entries.append(JFFS2Entry(type=ftype, path=fpath, symlink=symlink, uid=uid, guid=guid, permissions=permissions))

        return entries

    def extract_entry(self, entry):
        outfile = os.path.join(self.directory, entry.path)

        if self.verbose:
            sys.stderr.write(entry.path + "\n")

        if entry.type == 'd':
            try:
                os.mkdir(outfile)
            except OSError as e:
                pass
                #sys.stderr.write("Failed to create directory '%s': %s\n" % (outfile, str(e)))
        elif entry.type == 'l':
            try:
                os.symlink(entry.symlink, outfile)
            except OSError as e:
                pass
                #sys.stderr.write("Failed to create symlink '%s -> %s': %s\n" % (outfile, entry.symlink, str(e)))
        elif entry.type == '-':
            # jffs2reader self.image -f entry.path
            (stdout, stderr) = subprocess.Popen(['jffs2reader', self.image, '-f', entry.path],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE).communicate()

            if stderr:
                pass
                #sys.stderr.write("jffs2reader error while reading file '%s': %s\n" % (entry.path, binwalk.core.compat.bytes2str(stderr)))
            else:
                fp = binwalk.core.common.BlockFile(outfile, "wb")
                fp.write(stdout)
                fp.close()
        # TODO: Add support for special device files
        #elif entry.type == 'c':
        #    pass
        else:
            #sys.stderr.write("Don't know how to handle file type '%c' for '%s'\n" % (entry.type, entry.path))
            return

        # Set file user/group owner
        try:
            os.chown(outfile, entry.uid, entry.guid)
        except OSError as e:
            pass

        # Set file permissions
        try:
            os.chmod(outfile, entry.permissions)
        except OSError as e:
            pass

    def extract(self):
        for entry in self.ls():
            self.extract_entry(entry)

class UnJFFS2Plugin(binwalk.core.plugin.Plugin):
    '''
    Extrator plugin for JFFS2 file systems.
    '''
    MODULES = ['Signature']

    def init(self):
        if self.module.extractor.enabled:
            self.module.extractor.add_rule(txtrule=None,
                                           regex='^jffs2 filesystem',
                                           extension='jffs2',
                                           cmd=self.extractor)

    def extractor(self, fname):
        fname = os.path.realpath(fname)
        outdir = os.path.join(os.path.dirname(fname), 'jffs2-root')
        outdir = binwalk.core.common.unique_file_name(outdir)

        try:
            UnJFFS2(fname, outdir).extract()
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            return False

        return True

