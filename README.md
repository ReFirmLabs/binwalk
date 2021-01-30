# Binwalk

原始的`binwalk`依赖要么是过时的，要么是过于恶心，为此，笔者修改了`dep.sh`，删去过时的`python2`，增加`pip`源，大幅提高国内用户的下载速度。

```
git clone https://github.com/liyansong2018/binwalk.git
cd binwalk
./dep.sh
sudo python3 setup.py install
```
