# -*- coding: utf-8 -*-
# @Time     : 2022/01/25 16:38:14
# @Author   : ddvv
# @Site     : https://ddvvmmzz.github.io
# @File     : test.py
# @Software : Visual Studio Code
# @WeChat   : NextB

import json
import ssdeep
import tlsh

def read_hash(file_name):
    with open(file_name, 'r') as f:
        datas = f.readlines()
        return [file_hash.strip() for file_hash in datas]

def ssdeep_compare(data1, data2):
    h1 = data1.get('ssdeep', '')
    h2 = data2.get('ssdeep', '')
    score = ssdeep.compare(h1, h2)

    return score/100.0

def tlsh_compare(data1, data2):
    h1 = data1.get('tlsh', '')
    h2 = data2.get('tlsh', '')
    score = tlsh.diff(h1, h2)

    return score

def vhash_compare(data1, data2):
    h1 = data1.get('tlsh', '')
    h2 = data2.get('tlsh', '')
    score = 1.0 if h1 == h2 else 0.0

    return score

def main():
    mmdt_hash_sim = read_hash('./mmdt_sim.txt')
    with open('./test.json', 'r') as f:
        vhash_json = json.loads(f.read())
    print('原始文件,相似文件,mmdt相似度,ssdeep相似度,tlsh相似度,vhash相似度,原始文件类型,相似文件类型')
    for mhs in mmdt_hash_sim:
        tmp = mhs.split(',')
        ori_hash = tmp[0]
        sim_hash = tmp[1]
        mmdt_sim = float(tmp[2])
        ori_data = vhash_json[ori_hash]
        sim_data = vhash_json[sim_hash]
        ssdeep_sim = ssdeep_compare(ori_data, sim_data)
        tlsh_sim = tlsh_compare(ori_data, sim_data)
        vhash_sim = vhash_compare(ori_data, sim_data)
        ori_type = ori_data.get('magic', '').split(' ')[0]
        sim_type = sim_data.get('magic', '').split(' ')[0]
        print('%s,%s,%.3f,%.3f,%.3f,%.3f,%s,%s' % (
            ori_hash,sim_hash,mmdt_sim,ssdeep_sim,tlsh_sim,vhash_sim,ori_type,sim_type
        ))


if __name__ == '__main__':
    main()
