Description
===========

The binwalk python module can be used by any python script to programmatically perform binwalk scans and obtain the results of those scans. 

The classes, methods and objects in the binwalk modules are documented via pydoc, including examples, so those interested in using the binwalk module are encouraged to look there. However, several common usage examples are provided here to help jump-start development efforts.


Binwalk Scripting
=================

Each of binwalk's features (signature scans, entropy analysis, etc) are implemented as separate modules. These modules can be invoked via `binwalk.execute`.

In fact, the binwalk command line utility can be duplicated nearly entirely with just two lines of code:

```python
import binwalk
binwalk.execute()
```

The `execute` function accepts both args and kwargs, which correspond to the normal command line options accepted by the binwalk command line utility, providing a large amount of freedom in how you choose to specify binwalk options (if none are specified, sys.argv is used by default).

For example, to execute a signature scan, you at the very least have to specify the `--signature` command line option, as well as a list of files to scan. This can be done in a number of ways:

```python
binwalk.execute('firmware1.bin', 'firmware2.bin', signature=True)

binwalk.execute('firmware1.bin', 'firmware2.bin', **{'signature' : True})
        
binwalk.execute(*['firmware1.bin', 'firmware2.bin'], signature=True)
        
binwalk.execute(*['--signature', 'firmware1.bin', 'firmware2.bin',])

binwalk.execute('--signature', 'firmware1.bin', 'firmware2.bin')
```

All args and kwargs keys/values correspond to binwalk's command line options. Either args or kwargs, or a combination of the two may be used, with the following caveats:

* All command line switches passed via args must be preceeded by hyphens (not required for kwargs)
* All file names must be passed via args, not kwargs

Accessing Scan Results
======================

`binwalk.execute` returns a list of objects. Each object corresponds to a module that was run. For example, if you specified `--signature` and `--entropy`, then both the Signature and Entropy modules would be executed and you would be returned a list of two objects.

The two attributes of interest for each object are the `results` and `errors` objects. Each is a list of binwalk.core.module.Result and binwalk.core.module.Error objects respectively. Each Result or Error object may contain custom attributes set by each module, but are guarunteed to have at least the following attributes (though modules are not required to populate all attributes):

|  Attribute  | Description |
|-------------|-------------|
| offset      | The file offset of the result/error (usually unused for errors) |
| description | The result/error description, as displayed to the user |
| module      | Name of the module that generated the result/error |
| file        | The file object of the scanned file |
| valid       | Set to True if the result if value, False if invalid (usually unused for errors) |
| display     | Set to True to display the result to the user, False to hide it (usually unused for errors) |
| extract     | Set to True to flag this result for extraction (not used for errors) |
| plot        | Set to Flase to exclude this result from entropy plots (not used for errors) |

binwalk.core.module.Error has the additional guarunteed attribute:

|  Attribute  | Description |
|-------------|-------------|
| exception   | Contains the Python execption object if the encountered error was an exception |

Thus, scan results and errors can be programatically accessed rather easily:

```python
for module in binwalk.execute('firmware1.bin', 'firmware2.bin', signature=True):
    print ("%s Results:" % module.name)
    for result in module.results:
        print ("\t%s    0x%.8X    %s" % (result.file.name, result.offset, result.description))
```

Module Exceptions
=================

The only expected exception that should be raised is that of binwalk.ModuleException. This exception is thrown only if a required module encountered a fatal error (e.g., one of the specified target files could not be opened):

```python
try:
    binwalk.execute()
except binwalk.ModuleException as e:
    print ("Critical failure:", e)
```
