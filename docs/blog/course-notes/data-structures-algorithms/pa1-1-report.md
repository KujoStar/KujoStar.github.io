---
id: pa1-1-report
title: PA1-1 Report
date: '2023-01-20'
updated: '2023-01-20'
description: 通过压位存储实现高精度整数乘法。
tags:
- DSA解题报告
---

## 一、题目大意 {#一、题目大意}


给定$n$组数据a,b，求出$a \times b$。  
其中$n \leq 500, 0 \leq a,b \leq 10^{5000}$。


## 二、算法选择 {#二、算法选择}


设相乘的数的位数最多为$m$，则朴素算法的复杂度为$O(nm^2)$，在本题的数据范围下会造成超时。

于是考虑进行压缩位数的操作，假设压缩$k$位。为了防止在运算过程中压位存储地数组元素出现溢出，$k$的取值需要满足不等式

解得$k <= 8, k \in \mathbb{Z}$。同时，显然压位后的算法时间复杂度为$\displaystyle O(\frac{m^2}{k^2})$，其中$m$为两个乘数的最大位数。因此，$k$需要尽可能地取大。因此我们选择$k=8$，即压八位进行存储（采用$10^8$进制），并进行后续的运算。


## 三、代码实现 {#三、代码实现}


为此我们定义函数`change_to_number`，从最末尾开始，使用`strncpy`函数每八位截取一段，通过`atoi()`函数转换为八位正整数，顺序存放在数组`n`中，并返回最终数组`n`的位数，也即代码中的`now`。  

```cpp
const int w = 8;//压缩存储的位数
int change_to_number(char s[], long long n[]) {
	char temp[MAX];
	int len = strlen(s);
	int now = 0;
	while(len / w){
		strncpy(temp,s + len - w, w);
		n[now] = atoi(temp);
		len -= w;
		now ++;
	}
	if(len){
		memset(temp, 0, sizeof(temp));
		strncpy(temp, s, len);
		n[now] = atoi(temp);
		now ++;
	}
	return now;
}
```


定义函数`mul`，对两个处理好的存放着八位整数的数组`a`，`b`进行模拟竖式乘法运算，合理处理进位，获得结果。  

```cpp
const int jw = 1e8;//压位算法下的进制
void mul(long long a[], long long b[], long long c[], int m, int n) {
	for(int i = 0;i < m;i++){
		for(int j = 0;j < n;j++){
			c[i + j] += a[i] * b[j];
			c[i + j + 1] += c[i + j] / jw;
			c[i + j] = c[i + j] % jw;
		}
	}
	return;
}
```


定义函数`print_out()`，对结果数组进行输出。从第一个不是0的一位开始，依次向前输出，不足八位的采用`printf("%0*d")`的方法补足0，这样就完成了对结果的输出。此处需要特殊判断，若结果为0，则手动输出0。  

```cpp
void print_out(long long a[]) {
	bool check = false;
	for(int i = 10004;i >= 0;i--){
		if(a[i] != 0){
			check = true;
			printf("%d", a[i]);
			for(int j = i - 1;j >= 0;j--){
				printf("%0*d", w, a[j]);
			}
			printf("\n");
			break;
		}
	}
	if(check == false) {
		cout << "0" << endl;
	}
}
```



## 四、复杂度分析 {#四、复杂度分析}


本题中，设每次计算的两个乘数的位数为$p,q$，算法的时间复杂度为$O(pq)$，空间复杂度为$O(p+q)$。
