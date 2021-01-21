---
title: "python_mmdt:从0到1--实现简单恶意代码分类器(二)"
published: true
---

## 概述

上篇文章[python_mmdt:一种基于敏感哈希生成特征向量的python库(一)](https://ddvvmmzz.github.io/python_mmdt-%E4%B8%80%E7%A7%8D%E5%9F%BA%E4%BA%8E%E6%95%8F%E6%84%9F%E5%93%88%E5%B8%8C%E7%94%9F%E6%88%90%E7%89%B9%E5%BE%81%E5%90%91%E9%87%8F%E7%9A%84python%E5%BA%93(%E4%B8%80))我们介绍了一种叫`mmdt_hash`（mmdt敏感哈希）生成方法，并对其中的概念做了基本介绍。本篇，我们重点谈谈`mmdt_hash`的分类应用场景。

## 需求场景

设想这么一个需求场景：有一批文件需要判定是否属于恶意文件，并且需要给出恶意文件所属的家族类型。这个需求该怎么高效处理呢？处理过程又该怎么固化成我们自己的经验呢？当以后面临同样的需求时，能否复用之前的结果呢？

我能想到的方法有以下三种：

* 方法一：本地下载安装杀毒软件，使用杀毒软件对这批文件进行扫描，查看检测结果。
* 方法二：将这些文件上传到诸如Virustotal之类的检测平台，查看检测结果。
* 方法三：随机抽取样本分析，提取yara规则，利用yara规则对剩余文件进行扫描，未扫出的文件继续人工分析，继续提yara规则，如此反复，直到处识别所有文件。

针对以上三种方法，分别讨论其优点和缺点：

* 方法一：
  * 优点：处理方式简单快捷，误报率极低，处理效率高
  * 缺点：单一杀软漏报率可能较高；在Linux/MacOS上安装、使用杀软不方便；处理过程很难固化为经验；有可能导致文件泄漏（备注：联网使用杀软云查可能导致文件被收集）
* 方法二：
  * 优点：适用Windows/Linux/MacOS平台；检测误报率、漏报率都极低，结果丰富；处理效率高
  * 缺点：有联网要求，不适用隔离环境；有一定的代码开发工作；文件百分百泄漏
* 方法三：
  * 优点：处理过程天然可固化为经验；适用任意平台；适用隔离网络；经验可积累，可复用；保证文件私密性
  * 缺点：工作量极大，处理效率极低；人工分析经验要求高

上诉需求场景或许太过特殊化，但是有一定的代表性。针对上述的需求场景，使用`python_mmdt`工具的分类功能，可以很好的解决上述问题。

使用`python_mmdt`工具的分类功能，具有以下优点：

* 处理方式简单、快捷、处理效率高
* 可打包为可执行文件，附带特征向量集合，跨平台适用Windows/Linux/MacOS
* 无联网要求，适用隔离网，文件保密性高
* 处理过程可固化为经验，经验固化方式简单，处理结果方便积累、复用
* `mmdt_hash`大小固定，特征向量集合存储占用空间小

另外，`mmdt_hash`同时支持高性能、分布式计算，对比`ssdeep`，拥有更广的使用场景。同时，有三个不足需要特别指出：

* 准确率可能较低（依赖于判定分值的设定）
* 漏报率可能较高（依赖于判定分值的设定）
* 部分文件的`mmdt_hash`值没有意义，不能用作分类规则。

因此，可以在不同的场景使用不同的判定分值，判定分值越高，准确率越高；判定分值越低，漏报率越低。如判定分值设定为1.0，则几乎没有误报；如判定分值设定设定为0.85，则比判定分值设为0.95的漏报率更低。

## 代码项目地址

* [python_mmdt](https://github.com/a232319779/python_mmdt)
* 版本：0.1.3
* 特性：实现简单分类器，项目附带基础敏感哈希特征库，可实现恶意样本匹配

## 命令汇总

使用`pip`安装（安装过程见上一篇文章）`python_mmdt`之后，会向系统中添加如下命令：

* mmdt-hash：计算指定文件的`mmdt_hash`值
* mmdt-std：计算`mmdt_hash`的标准差，用于衡量`mmdt_hash`的好坏
* mmdt-compare：比较两个文件的`相似度`
* mmdt-gen：利用已知样本集，生成基于`mmdt_hash`的特征向量集合
* mmdt-filter：对生成的的特征向量集合，进行过滤，移除`坏`特征向量
* mmdt-filter-simple：对生成的特征向量集，进行简单过滤（去重），适用于简单分类器
* mmdt-copy：拷贝特征向量集合文件或特征向量集合标签文件到工具库目录
* mmdt-classify：核心功能，对未知样本集进行分类处理，输出分类结果

## 命令介绍

### 1. 计算文件的`mmdt_hash`命令：`mmdt-hash`

* 功能：计算单个文件`mmdt_hash`值
* 输入参数1：文件路径
* 屏幕输出：`mmdt_hash`的值
* 文件输出：无

```sh
# ➜ mmdt-hash APT28_1
#   5D58573C:B39A90BCDCB4D491BEC74B207AE5FE39
$ mmdt-hash $file
```

`mmdt_hash`值结构如：`"index_hash:value_hash"`，`index_hash`是4字节敏感哈希索引，`value_hash`是16字节敏感哈希值，两个哈希值之间使用`:`冒号隔开。敏感哈希索引用于**快速**定位相似哈希；敏感哈希值用于计算两个`mmdt_hash`之间的相似度。

### 2. 计算`mmdt_hash`标准差命令：`mmdt-std`

* 功能：计算单个`mmdt_hash`值的标准差
* 输入参数1：单个`mmdt_hash`值
* 屏幕输出：`mmdt_hash`值的标准差
* 文件输出：无

```sh
# ➜ mmdt-std 5D58573C:B39A90BCDCB4D491BEC74B207AE5FE39
#   standard deviation: 45.333946
$ mmdt-std $mmdt_hash_str
```

`mmdt_hash`值的标准差，用于衡量生成的`mmdt_hash`的好坏。从大量统计结果看，当标准差低于10.0左右时，计算生成的`mmdt_hash`
的有效性太差，不能有效表示原始文件。

### 3. 计算两个文件相似度命令：`mmdt-compare`

* 功能：计算两个文件的相似度
* 输入参数1：文件1路径
* 输入参数2：文件2路径
* 屏幕输出：两个文件的相似度
* 文件输出：无

```sh
# ➜ mmdt-compare APT28_1 APT28_2
#   0.9929302916167373
$ mmdt-compare $file1 $file2
```

计算两个输入文件的相似度，相似度本质采用欧几里得距离衡量。计算两个`mmdt_hash`的欧几里得距离，并进行归一化处理，得到相似度。

### 4. 生成特征向量集合命令：`mmdt-gen`

* 功能：核心功能之一，生成基于`mmdt_hash`的特征向量集合
* 输入参数1：已知样本集的路径
* 输入参数2：已知样本集的标签文件路径
* 屏幕输出：生成特征向量过程信息
* 文件输出：当前文件夹生成两个文件，`mmdt_feature.label`和`mmdt_feature.data`

```sh
# ➜ mmdt-gen APT28 apt28.tags
#   ...
#   process: APT28_3, 22
#   process: APT28_4, 23
#   end gen mmdt set.
# ➜ ll mmdt_feature.*
#   -rw-r--r--  1 ddvv  staff   703B  1 16 10:34 mmdt_feature.data
#   -rw-r--r--  1 ddvv  staff   133B  1 16 10:34 mmdt_feature.label
$ mmdt-gen $file_path $file_tag
```

遍历指定文件目录，计算该目录下所有文件的`mmdt_hash`，并从标签文件中读取对应标签，生成标签索引，组合到特征向量集合中。输入的标签文件采用`文件名,标签`的`csv`格式存储，如`APT28_1,group_apt28`。`mmdt_feature.label`是本特征向量集合的标签文件，用于将标签索引还原为原始名称；`mmdt_feature.data`是特征向量集合文件。两文件都使用`pickle`序列化，同时使用`zip`压缩保存。

### 5. 特征向量过滤命令：`mmdt-filter`

* 功能：对生成的特征向量集合进行通用过滤处理
* 输入参数1：特征向量集合文件
* 输入参数2：过滤条件的标准差下限
* 屏幕输出：过滤特征向量过程信息
* 文件输出：覆盖输入的**特征向量集合文件路径**

```sh
# ➜ mmdt-filter mmdt_feature.data 10.0
#   start filter mmdt set.
#   old len: 23
#   new len: 21
#   end filter mmdt set.
# ➜ ll mmdt_feature.*
#   -rw-r--r--  1 ddvv  staff   689B  1 16 10:39 mmdt_feature.data
#   -rw-r--r--  1 ddvv  staff   133B  1 16 10:34 mmdt_feature.label
$ mmdt-filter $mmdt_feature_file_name $dlt
```

特征向量集合的通用过滤方法，计算特征向量集合中`mmdt_hash`值的标准差，移除标准差小于10.0的`mmdt_hash`。如前所述，标准差小于10.0的`mmdt_hash`有效性很低，无法使用。

### 6. 简单分类器特征向量过滤命令：`mmdt-filter-simple`

* 功能：对生成的`mmdt_hash`特征向量集合进行适配简单分类器(去重)过滤处理
* 输入参数1：特征向量集合文件
* 屏幕输出：过滤特征向量过程信息
* 文件输出：覆盖当前路径的`mmdt_feature.data`文件

```sh
# ➜ mmdt-filter-simple mmdt_feature.data
#   start filter mmdt set.
#   old len: 21
#   new len: 21
#   end filter mmdt set.
# ➜ ll mmdt_feature.*
#   -rw-r--r--  1 ddvv  staff   689B  1 16 10:39 mmdt_feature.data
#   -rw-r--r--  1 ddvv  staff   133B  1 16 10:34 mmdt_feature.label
$ mmdt-filter-simple $mmdt_feature_file_name
```

简单分类算法的特定过滤方式，移除完全相同的特征向量，并覆盖原始特征向量集合。

### 7. 特征拷贝命令：`mmdt-copy`

* 功能：将特征向量集合文件或特征向量集合标签文件拷贝到工具库目录
* 输入参数1：特征向量集合文件或特征向量集合标签文件
* 屏幕输出：无
* 文件输出：无

```sh
# ➜ mmdt-copy mmdt_feature.data
# ➜ mmdt-copy mmdt_feature.label
$ mmdt-filter-simple $mmdt_feature
```

需要将特征向量集合文件或特征向量集合标签文件拷贝到工具目录，才可正常使用分类功能。

### 8. 分类器使用命令：`mmdt-classify`

* 功能：核心功能之一，对指定文件或文件夹进行分类识别
* 输入参数1：目标文件路径或文件夹路径
* 输入参数2：相似度判定分值下限，可选，默认0.95
* 输入参数3：分类器类型，可选，默认1，简单分类器
* 屏幕输出：分类过程结果输出
* 文件输出：无

**重要说明**：

需要将生成的`mmdt_feature.label`和`mmdt_feature.data`文件拷贝到`python_mmdt`的安装路径，命令如下：

* 拷贝特征向量集文件：`mmdt-copy mmdt_feature.data`
* 拷贝特征向量集对应标签文件：`mmdt-copy mmdt_feature.label`

**特别注意：**

* **`mmdt_feature.label`和`mmdt_feature.data`文件名不可更改**
* **当缺失`mmdt_feature.data`文件时，分类器默认使用`python_mmdt`库提供的特征向量集**
* **当缺失`mmdt_feature.label`文件时，分类器仍可以工作，但判定结果仅输出是否匹配文件，而不会给出对应的判定标签**

```sh
# ➜ mmdt-classify . 0.8 1
#   ...
#   ./APT28_5,1.000000,group_apt28,39.660364
#   ./APT28_2,0.992930,group_apt28,44.917703
#   ./APT28_23,1.000000,group_apt28,39.682770
#   ...
# 注意：缺失mmdt_feature.label文件时，只会输出是否匹配，而不会输出对应标签，match_0表示匹配0号标签索引
# ➜ mmdt-classify . 0.8 1
#   ...
#   ./APT28_5,1.000000,matched_0,39.660364
#   ./APT28_2,0.992930,matched_0,44.917703
#   ./APT28_23,1.000000,matched_0,39.682770
#   ...
$ mmdt-classify $file_or_path $sim_value $classify_type
```

`python_mmdt`的核心功能，实现未知样本的快速识别。`mmdt-classify . 0.8 1`表示对`当前目录`下的文件进行分类，分类判定分值设定为`0.8`，分类算法采用`1`（简单分类算法）。

## 总结

本篇主要介绍了`python_mmdt`的一种简单分类应用。在实际使用简单分类器时，`python_mmdt`会将特征向量集合转成简单分类特征库，通过查找相等的索引哈希，计算对应`mmdt_hash`的相似度，满足判定分值，则返回判定结果。利用`python_mmdt`，可以实现自动特征的提取、积累、复用，通过不断的积累，期待实现“见过即可查”的目标。

另外，目前`python_mmdt`直接对压缩包类型的文件计算敏感哈希，其`mmdt_hash`值常常不可用，后续会尝试对压缩包进行解压缩，计算实际文件。当前使用哈希索引匹配的的方式，虽然效率高，但是漏报率也高。后续会尝试使用KNN算法对特征向量集合进行计算，提高基检出率。

![](https://p2.ssl.qhimg.com/t0144c96316fd517e5f.png)

如果恶意代码分析人员，可以共建一个`mmdt_hash`特征向量库，一定可以大大方便恶意代码分析这件事。设想一下，每个特征向量20个字节，1亿条特征向量的集合大小在2G左右，1亿条特征向量可以检出的恶意代码数量可能达到上百亿，上千亿，提供的恶意代码检测覆盖面就广阔的多了。**更重要的**，共享`mmdt_hash`值不会导致原始文件信息的泄漏，同时又能提供非常有价值的信息。
