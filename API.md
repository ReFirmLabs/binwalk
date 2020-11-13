Description
===========

The binwalk python module can be used by any python script to programmatically perform binwalk scans and obtain the results of those scans. 

The classes, methods and objects in the binwalk modules are documented via pydoc, including examples, so those interested in using the binwalk module are encouraged to look there. However, several common usage examples are provided here to help jump-start development efforts.


Binwalk Scripting
=================

Each of binwalk's features (signature scans, entropy analysis, etc) are implemented as separate modules. These modules can be invoked via `binwalk.scan`.

In fact, the binwalk command line utility can be duplicated nearly entirely with just two lines of code:

```python
import binwalk
binwalk.scan()
```

The `scan` function accepts both args and kwargs, which correspond to the normal command line options accepted by the binwalk command line utility, providing a large amount of freedom in how you choose to specify binwalk options (if none are specified, `sys.argv` is used by default).

For example, to execute a signature scan, you at the very least have to specify the `--signature` option, as well as a list of files to scan. This can be done in a number of ways:

```python
binwalk.scan('--signature', 'firmware1.bin', 'firmware2.bin')

binwalk.scan('firmware1.bin', 'firmware2.bin', signature=True)

binwalk.scan('firmware1.bin', 'firmware2.bin', **{'signature' : True})
        
binwalk.scan(*['firmware1.bin', 'firmware2.bin'], signature=True)
        
binwalk.scan(*['--signature', 'firmware1.bin', 'firmware2.bin',])
```

All args and kwargs keys/values correspond to binwalk's command line options. Either args or kwargs, or a combination of the two may be used, with the following caveats:

* All command line switches passed via args must be preceded by hyphens
* All file names must be passed via args, not kwargs

There is one available API argument which is not exposed via the command line: the `string` argument. When `string` is set to True, data to be scanned can be passed directly to the binwalk module, rather than a file name:

```python
data = "This is some data to scan for signatures"
binwalk.scan(data, signature=True, string=True)
```

Accessing Scan Results
======================

`binwalk.scan` returns a list of objects. Each object corresponds to a module that was run. For example, if you specified `--signature` and `--entropy`, then both the `Signature` and `Entropy` modules would be executed and you would be returned a list of two objects.

The two attributes of greatest interest for each object are the `results` and `errors` objects. Each is a list of `binwalk.core.module.Result` and `binwalk.core.module.Error` instances, respectively. Each `Result` or `Error` instance may contain custom attributes set by each module, but are guaranteed to have at least the following attributes (though modules are not required to populate all attributes):

|  Attribute  | Description |
|-------------|-------------|
| offset      | The file offset of the result/error (usually unused for errors) |
| description | The result/error description, as displayed to the user |
| module      | Name of the module that generated the result/error |
| file        | The file object of the scanned file |
| valid       | Set to True if the result is valid, False if invalid (usually unused for errors) |
| display     | Set to True to display the result to the user, False to hide it (usually unused for errors) |
| extract     | Set to True to flag this result for extraction (not used for errors) |
| plot        | Set to False to exclude this result from entropy plots (not used for errors) |

binwalk.core.module.Error has the additional guaranteed attribute:

|  Attribute  | Description |
|-------------|-------------|
| exception   | Contains the Python exception object if the encountered error was an exception |

Thus, scan results and errors can be programatically accessed rather easily:

```python
for module in binwalk.scan('firmware1.bin', 'firmware2.bin', signature=True, quiet=True):
    print ("%s Results:" % module.name)
    for result in module.results:
        print ("\t%s    0x%.8X    %s" % (result.file.path, result.offset, result.description))
```

Note the above use of the `--quiet` option which prevents the binwalk module from printing its normal output to screen.

Each module object will also have an additional `extractor` attribute, which is an instance of the `binwalk.modules.extractor.Extractor` class. Of particular use is `binwalk.modules.extractor.Extractor.output`, a dictionary containing information about carved/extracted data:

```python
for module in binwalk.scan(sys.argv[1], signature=True, quiet=True, extract=True):
    for result in module.results:
        if result.file.path in module.extractor.output:
            # These are files that binwalk carved out of the original firmware image, a la dd
            if result.offset in module.extractor.output[result.file.path].carved:
                print "Carved data from offset 0x%X to %s" % (result.offset, module.extractor.output[result.file.path].carved[result.offset])
            # These are files/directories created by extraction utilities (gunzip, tar, unsquashfs, etc)
            if result.offset in module.extractor.output[result.file.path].extracted:
                print "Extracted %d files from offset 0x%X to '%s' using '%s'" % (len(module.extractor.output[result.file.path].extracted[result.offset].files),
                                                                                  result.offset,
                                                                                  module.extractor.output[result.file.path].extracted[result.offset].files[0],
                                                                                  module.extractor.output[result.file.path].extracted[result.offset].command)
```


Module Exceptions
=================

The only expected exception that should be raised is that of binwalk.ModuleException. This exception is thrown only if a required module encountered a fatal error (e.g., one of the specified target files could not be opened):

```python
try:
    binwalk.scan()
except binwalk.ModuleException as e:
    print ("Critical failure:", e)
```
