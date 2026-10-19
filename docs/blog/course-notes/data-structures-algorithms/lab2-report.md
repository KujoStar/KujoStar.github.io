---
id: lab2-report
title: Lab2 Report
date: '2023-01-26'
updated: '2023-01-26'
tags:
- DSA解题报告
---

本次lab需要实现一个字符串的哈希策略,实现多种哈希函数和冲突处理策略并分析性能。


## 一、哈希函数和冲突处理策略的实现 {#一、哈希函数和冲突处理策略的实现}


#### 坏的哈希函数的实现方法 {#坏的哈希函数的实现方法}


```cpp
int bad_hashing::operator()(char* str, int N){
    long long res = 0;
    int len = strlen(str);
    for(int i = 0; i < len; i ++) {
        res += int(str[i]);
    }
    return res % N;
}//坏的哈希函数，简单相加ascii码
```


实现坏的哈希函数，考虑直接相加字符串中所有字符的Ascii码，最后对哈希表大小取模。在这种哈希策略下，某个字符的变化导致Ascii码变化，很大概率直接导致最终结果的变化。


#### 好的哈希函数的实现方法 {#好的哈希函数的实现方法}


```cpp
int good_hashing::operator()(char *str, int N) {
    long long res = 0;
    int seed = 97;
    int seed2 = 53;
    int len = strlen(str);
    for(int i = 0; i < len; i ++) {
        res = res * seed + int(str[i]) * seed2;
    }
    return res % N;
}
```


实现好的哈希函数，考虑如下方法：随机选取两个质数作为种子（此处选取了97和53），以种子为倍数将结果不断加上每一位字符的Ascii码，这样就实现了利用所有字符的哈希策略。其递推式如下：，为了与哈希表大小相适配，最终返回的结果为


#### 双向平方探测策略的实现方法 {#双向平方探测策略的实现方法}


实现过程中，采用一个`bool`值来控制探测的方向，每次探测后都将探测步长+1，同时注意对哈希表大小取模。本题中的实现默认先向左探测，则步长为$x$时的探测结果为 代码实现如下：  

```cpp
int square_probe::operator()(hash_entry* Table, int table_size, int last_choice) {
    if(direct) {
        direct = false;
        int temp = cnt++;
        int res = last_choice - ((1ll * temp * temp) % table_size);
        while(res < 0) {
            res += table_size;
        }
        return res;
    }//向左探测，偏移量为cnt^2（注意取模）
    else {
        direct = true;
        int temp = cnt++;
        int res = last_choice + ((1ll * temp * temp) % table_size);
        while(res >= table_size) {
            res -= table_size;
        }
        return res;
    }//向右探测，偏移量为cnt^2（注意取模）
}
```



#### 公共溢出区策略的实现方法 {#公共溢出区策略的实现方法}


思路为，若检测到处理冲突的策略为公共溢出区策略，则将哈希表大小减小为`TABLE_SIZE/2`，另一半作为公共缓冲区依次存放冲突字符串。代码实现如下：  

```cpp
int overflow::operator()(hash_entry* Table, int table_size, int last_choice) {
    int temp = pos++;//pos为在公共缓冲区的位置序号
    return (TABLE_SIZE / 2 + temp);//这里设置公共溢出区的大小为总表大小一半
}
```



## 二、测试数据的构造 {#二、测试数据的构造}


构造数据的方式为读取命令行参数，共设置了三个参数，第一个参数表示是否随机进行插入与查询操作，0表示按照先插入后查询的顺序，1表示随机顺序；第二个参数为插入操作的次数；第三个参数为查询操作的次数。在本题中，预先定义了结构体变量`user`以存储用户信息，并定义成员函数以方便直接输出，采用大小为`5e5`的`vector`来存放原始数据。  

```cpp
struct user {
    int rank;//用户排名
    string name;//用户id
    void to_insert() {
        cout << "0 " << this->name << " " << this->rank << endl;
    }//输出插入的信息
    void to_search() {
        cout << "1 " << this->name << endl;
    }//输出查询的信息
};
vector<user> users(5e5);//存放poj.txt中的数据
```

  
以下为数据的读入以及预处理。若`if_random`值为1，则表示需要随机顺序，于是采用`mt19937`方法产生随机数`rng()`，然后`shuffle(op.begin(), op/end(), rng)`即可、  

```cpp
int if_random = atoi(argv[1]);
int insert_time = atoi(argv[2]);
int search_time = atoi(argv[3]);//获取参数
vector<int > op;//操作符集合
for(int i = 0; i < insert_time; i ++) {
    op.push_back(0);//插入操作
}
for(int i = 0; i < search_time; i ++) {
    op.push_back(1);//查询操作
}
```

  
需要注意的是，在插入数据的时候，由于原数据具有随机性，同时为了保证插入操作的唯一性，则考虑对序号`range(0, 500000)`进行`shuffle`，之后按序读取随机排列后的序号，再插入对应的数据即可。  

```cpp
shuffle(pos.begin(), pos.end(), rng);//pos为0-499999的随机排列
int cnt = 0;
for(int i = 0; i < op.size(); i ++) {
    if(op[i] == 0) {
        users[pos[cnt++]].to_insert();
    }
    if(op[i] == 1) {
        int sop = rand() % 500000;
        users[pos[sop]].to_search();
    }
}
```



## 三、测试结果分析 {#三、测试结果分析}


1. “好”的哈希函数的性能显著占优，因为其在每次迭代时都先把原来的结果乘以某个质数再迭代，使得结果尽可能快地增大，这样在取模时尽可能降低了出现冲突的概率。

2. 双向平方试探策略的性能更好，因为双向平方试探策略可以更快地离开冲突聚集区，从而可以更快地找到可供存放冲突字符串的位置。

3. 对于“坏”的哈希函数，公共溢出区策略性能优于线性探测，劣于双向平方探测；对于“好”的哈希函数，公共溢出区策略性能均占优。结合实际情况，总体来看开放散列更占优。当装填数据较多，装填因子较大时，封闭散列会更占优。

4. 可能会提高在当前哈希策略下出现聚集冲突的概率。

5. 采用链地址法，若当前插入的元素触发扩容，就将哈希表大小扩大为原来的两倍，然后采用分摊转移的方法，先转移第一个不为空的桶到新的哈希表，然后将该元素插入。下一次插入时继续转移旧哈希表中第一个不为空的桶，再插入元素，直至旧哈希表为空为止。缩容一般出现在装填因子过小时，直接将哈希表大小缩减即可。



## 四、对实验框架做出的必要修改 {#四、对实验框架做出的必要修改}


在实现公共溢出区策略时，为了判断当前传入的策略是否是公共溢出区策略，我在基类结构体`collision_strategy`中增加了一个成员变量`type`，表示策略种类。`type=1`代表线性探测，`type=2`代表双向平方探测，`type=3`代表公共溢出区策略。这样，我们可以修改`insert`函数，加上对`type`值的判断，若`type=3`，代表执行公共溢出区策略，此时将`table_size`修改为一半即可，如下所示。  

```cpp
if(my_collision->type == 3) {
    table_size = TABLE_SIZE / 2;
}//如果type为3，表示策略为公共溢出区策略，则将table_size修改为一半
```
