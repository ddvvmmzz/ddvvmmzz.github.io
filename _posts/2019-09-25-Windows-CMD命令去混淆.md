---
title: "windows CMD命令去混淆脚本"
published: true
---

## 概述

利用python脚本实现cmd命令的去混淆功能。去混淆的目的是为了方便批量提取CC，同时方便了解执行流程。

<!--more-->

## 常规CMD命令符号一览
首先，一起回顾下CMD命令中常使用的命令符号，了解符号的意义，有助于掌握命令的意义与逻辑，以及了解去混淆的时机。

* @：隐藏命令的回显。
* ~：变量扩展或者扩展环境变量指定位置的字符串。
* %：引用环境变量或者单个%表示引用命令行参数。 
* ^： 取消转义字符。
* &： 命令连接字符。
* |： 管道符，将上一个命令的输出,作为下一个命令的输入。
* :： 标签符,接受goto命令所指向的标签。
* ""：界定符,使用带有空格的路径时用""将路径括起来。
* /： 其后的字符是命令的功能开关。
* \>： 命令重定向符，输入在前，输出在后，覆盖之前的内容。
* \>\>： 命令重定向符。输入在前，输出在后，不覆盖之前的内容。
* <：将后面文件的内容输出到前面。 
* = ：赋值符号,用于变量赋值。
* \ ：当前路径所在的根路径。
* && ：连接两个命令,&&前的命令成功时,才执行&&后的命令。
* || ：连接两个命令,||前的命令失败时,才执行||后的命令。
* $：findstr命令中表示一行的结束。
* ``：for/f中表示它们所包含的内容当作命令行执行并分析它的输出。
* !： 延迟变量,使用!!将变量名扩起来表示对变量值的引用。 

## CMD混淆介绍
介绍完常用命令符号，再介绍一下当前比较有名的混淆工具：**[Invoke-DOSfuscation](https://github.com/danielbohannon/Invoke-DOSfuscation)**。

该工具主要是用于混淆powershell脚本，同时兼容混淆cmd命令，详情参考[fireeye白皮书](https://www.fireeye.com/blog/threat-research/2018/03/dosfuscation-exploring-obfuscation-and-detection-techniques.html)

据作者自己介绍，他是在研究APT攻击的过程中对命令混淆这块产生的兴趣，并花了几个月的时间完成了这个混淆工具。作者本意是为了方便defenders去测试自己产品对混淆技术的检测能力。（PS：不过，考虑到实际情况，这个工具被攻击者用来躲避杀软检测的可能性更高。）

详细说明请参考该项目的[README]([https://github.com/danielbohannon/Invoke-DOSfuscation/blob/master/README.md](https://github.com/danielbohannon/Invoke-DOSfuscation/blob/master/README.md))，这里就不展开介绍了。


## 已有CMD去混淆工具

为了检测命令混淆这类攻击，fireeye开发了基于[flare-qdb](https://github.com/fireeye/flare-qdb)的动态去混淆的工具[De-DOSfuscator](https://github.com/fireeye/flare-qdb/blob/master/doc/dedosfuscator.md)。

flare-qdb是一套基于Python和[Vivisect](https://github.com/vivisect/vivisect)的命令行交互式模拟执行工具。该工具主要用于记录恶意程序的执行过程的某些状态值，方便分析人员去发现和回溯。

De-DOSfuscator是基于flare-qdb的Python脚本，用于记录混淆Powershell脚本或混淆cmd命令执行过程，并从中提取出原始的powershell或cmd命令。使用手册参考[dedosfuscator.md](https://github.com/fireeye/flare-qdb/blob/master/doc/dedosfuscator.md)，详细介绍参考[cmd-and-conquer-de-dosfuscation-with-flare-qdb](https://www.fireeye.com/blog/threat-research/2018/11/cmd-and-conquer-de-dosfuscation-with-flare-qdb.html)一文。

## python脚本去混淆介绍

**重点说明：以上内容和本脚本基本无关。不看也不影响理解本脚本。只是这些内容都挺好，值得学习，作为知识储备。**

python脚本拆分为5个过程，实现去混淆，其中第2、第3、第4步是关键，可以通过不断优化这三个步骤，实现对更多混淆类型的去混淆支持。

### 1. 替换^符号

^符号用于取消转移。

在命令混淆中，常见于`s^Et`、`fin^Ds^Tr`、`E^ch^O`等

### 2. 通过`=`和`%`的规则，查找混淆变量

`=`用于赋值，`%%`用于取值。

本过程流程如下：

1. 提取混淆字符串中所有`=`的位置，保存为`equ_list`
2. 提取混淆字符串中所有`%`的位置，按奇偶位拆分为两个`odd_list`(索引为1,3,5,7,...)，`even_list`(索引为0,2,4,6,...)。`odd_list`保存`%%`符号对结束符号的索引，`even_list`保存`%%`符号对开始符号的索引，(0,1)，(2,3)，...称为一个`%%`符号对
3. 移除`odd_list`中小于`min(equ_list)`的值，移除`even_list`中小于`min(equ_list)`的值
4. 递归：定位目标`=`号位置，若`=`号位于`%%`符号对之间，并且离结束`%`最近，则提取变量名和变量值，替换原始字符串中的混淆变量；如果字符串中不存在`=`号，或者`=`号不在`%%`符号对之间，则退出递归，返回新字符串

### 3. 通过`set`关键字，查找混淆变量

`set`命令用于显示、设置或删除 cmd.exe 环境变量。

本过程流程如下：
1. 通过正则表达式匹配`set`命令，提取`=`两边的变量名和变量值
2. 替换原始字符串中的混淆变量，替换规则包括`%%%s:%%`，`%%%s%%`，`!%s!`，`:%s`，`%s`(替换过程按顺序执行，不可更改)
3. 递归如上流程，不存在`set`则退出递归，返回新字符串

### 4. 通过%:~n,m%关键字，查找混淆变量

`%.*:~n,m%`用于变量截断，提取指定数据

本过程流程如下：
1. 通过正则表达式匹配`%(.*?):~(.*?),(.*?)%`命令，提取变量字符串、提取`,`两边的起始位置和长度
2. 利用提取的字符串替换匹配的字符
3. 递归如上流程，不存在`%(.*?):~(.*?),(.*?)%`则退出递归，返回新字符串

### 5. 统一常用命令、程序名称

统一小写常用命令、程序名称，当前包括`['echo', 'set', 'explorer', 'temp']`

## 其他一些想法

* 比如不用去混淆，直接使用机器学习做检测；
* 比如按混淆类型分类团伙之类的

## 附录

git项目：[ddvv](https://github.com/a232319779/scripts)

脚本下载地址：[windows-cmd命令去混淆脚本](https://github.com/a232319779/scripts/blob/master/scripts/deDosfuscation.py)

PS：脚本写完几个月了，期间拖了几个月才完成文章，有时候觉得写文章比写代码还困难，以后尽量不要拖延文章。