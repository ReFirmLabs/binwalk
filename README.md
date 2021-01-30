# Binwalk

原始的`binwalk`依赖要么是过时的，要么是过于恶心，为此，笔者修改了`dep.sh`，删去过时的`python2`，增加`pip`源，大幅提高国内用户的下载速度。

用户再也不必去手动下载某些依赖或者修改`dep.sh`文件，只需要一下两步，即可轻松源码安装`binwalk`。
```
git clone https://github.com/liyansong2018/binwalk.git
cd binwalk
./dep.sh
sudo python3 setup.py install
```
