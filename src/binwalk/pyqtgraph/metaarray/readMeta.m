function f = readMeta(file)
info = hdf5info(file);
f = readMetaRecursive(info.GroupHierarchy.Groups(1));
end


function f = readMetaRecursive(root)
typ = 0;
for i = 1:length(root.Attributes)
    if strcmp(root.Attributes(i).Shortname, '_metaType_')
        typ = root.Attributes(i).Value.Data;
        break
    end
end
if typ == 0
    printf('group has no _metaType_')
    typ = 'dict';
end

list = 0;
if strcmp(typ, 'list') || strcmp(typ, 'tuple')
    data = {};
    list = 1;
elseif strcmp(typ, 'dict')
    data = struct();
else
    printf('Unrecognized meta type %s', typ);
    data = struct();
end

for i = 1:length(root.Attributes)
    name = root.Attributes(i).Shortname;
    if strcmp(name, '_metaType_')
        continue
    end
    val = root.Attributes(i).Value;
    if isa(val, 'hdf5.h5string')
        val = val.Data;
    end
    if list
        ind = str2num(name)+1;
        data{ind} = val;
    else
        data.(name) = val;
    end
end

for i = 1:length(root.Datasets)
    fullName = root.Datasets(i).Name;
    name = stripName(fullName);
    file = root.Datasets(i).Filename;
    data2 = hdf5read(file, fullName);
    if list
        ind = str2num(name)+1;
        data{ind} = data2;
    else
        data.(name) = data2;
    end
end

for i = 1:length(root.Groups)
    name = stripName(root.Groups(i).Name);
    data2 = readMetaRecursive(root.Groups(i));
    if list
        ind = str2num(name)+1;
        data{ind} = data2;
    else
        data.(name) = data2;
    end
end
f = data;
return;
end


function f = stripName(str)
inds = strfind(str, '/');
if isempty(inds)
    f = str;
else
    f = str(inds(length(inds))+1:length(str));
end
end



