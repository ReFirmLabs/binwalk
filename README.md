# Binwalk

原始的`binwalk`依赖要么是过时的，要么是过于恶心，为此，笔者修改了`dep.sh`。

用户再也不必去手动下载某些依赖或者修改`dep.sh`文件，只需要一下两步，即可轻松源码安装`binwalk`。
```
git clone https://github.com/liyansong2018/binwalk.git
cd binwalk
./dep.sh
sudo python3 setup.py install
```

修改点
- 删除过时的`python2`和一系列无法安装的`python2`依赖包
- 增加`cramfsprogs`的正确安装
- 合入`sasquatch`针对`gcc 10`以上版本的补丁，该补丁已提交`binwalk`原作者的项目
- 增加`pip`代理的国内源，大幅提高依赖下载速度
