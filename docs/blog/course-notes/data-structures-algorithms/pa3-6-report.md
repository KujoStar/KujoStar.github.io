---
id: pa3-6-report
title: PA3-6 Report
date: '2023-01-26'
updated: '2023-01-26'
description: 使用 k-d 树和空间剪枝求解多维最近邻查询。
tags:
- DSA解题报告
---

## 一、题目大意 {#一、题目大意}


本题中，给定$n$个$d$维向量$\mathbf{x}_1,\cdots,\mathbf{x}_n$，$q$次询问，每次寻味给出一个$d$维向量$\mathbf{x}$，求向量$\mathbf{x}$与给出的$n$个向量距离的平方的最小值。  
数据满足$2 \leq d \leq 5$，$1 \leq n \leq 10^5$，$1 \leq q \leq 2 \times 10^5$，所有向量每个分量的绝对值不超过$10^7$。


## 二、算法分析 {#二、算法分析}


由题意可知，本题是一个高维的最近邻查询问题。为高效处理多维空间的数据信息，因此考虑采用kd树进行存储与查询。


## 三、代码实现 {#三、代码实现}


为了实现kd树，首先我们定义一个结构体`Node`，含有成员数组`num`，并且定义一个`Node`类型的数组`point`用于存储给出的向量的信息。同时，定义数组`lc[N]`与`rc[N]`分别存储树中第$i$个结点的左儿子和右儿子的根节点编号。此外，对每个维度，我们需要维护在该维度上每个点对应的子树内最值，因此定义两个数组`max_number`和`min_number`进行存储。从而可得前期准备如下：  

```cpp
int lc[N],rc[N];
struct Node {
	int num[5];
} point[N];//存储给出的点
int max_number[5][N], min_number[5][N];//维护各个维度上的最大值与最小值
```

  
kd树建树的核心思想为，每次选择一个维度中的一个基准点之后按照这一维度上值的大小关系将这$n$个点构成的$k$维空间内的超长方体进行分割，之后向两侧的超长方体递归，从而可以建立kd树。为了尽量达到平均分割，我们选择所有点在这一维度上的分量值得中位数作为基准，因此我们需要获取$n$个值的中位数，也即将第$k$大的值置于序列第$k$位的`kth_element`算法。  
由于本课程使用的OJ禁用了`algorithm`库中的`nth_element`函数，因此需要手动实现。参考快速排序算法的实现过程：每次选定一个基准值，确定该基准值在整个序列中的位置，之后向两侧递归排序。而在此处，我们只需要确定中位数的位置即可，因此我们在确定基准值的位置之后，只需根据大小关系向含有位置$k$的一侧递归。综上我们可以手动实现`kth_element`算法，实现如下：  

```cpp
void kth_element_with_dim(int k, int left, int right, int kd) {
	if(left < right) {
        Node pmt = point[left];
        int i = left, j = right, temp = point[left].num[kd];
        while(i < j) {
            while(i < j && point[j].num[kd] >= temp) {
                j --;
            }
            if(i < j) {
                point[i ++] = point[j];
            }
            while(i < j && point[i].num[kd] < temp) {
                i ++;
            }
            if(i < j) {
                point[j --] = point[i];
            } 
        }
        point[i] = pmt;
        if(i == k) return;
		else if(i > k) {
			kth_element_with_dim(k, left, i - 1, kd);
		}
		else {
			kth_element_with_dim(k, i + 1, right, kd);
		}//根据大小关系向含有k的一侧递归即可
    }
    else {
        return;
    }
}//实现了algorithm中的nth_element方法
```

  
对于kd树中的每个结点，我们需要根据该结点的左右子树的信息来维护这个结点对应的超矩形的信息，也即`max_number`与`min_number`数组中的值。因此考虑定义如下的`maintain`函数：  

```cpp
void maintain(int x) {
	for(int i = 0; i < dim; i ++) {
		max_number[i][x] = min_number[i][x] = point[x].num[i];
	}
	if(lc[x]) {
		for(int i = 0; i < dim; i ++) {
			max_number[i][x] = max(max_number[i][x], max_number[i][lc[x]]);
			min_number[i][x] = min(min_number[i][x], min_number[i][lc[x]]);
		}
	}
	if(rc[x]) {
		for(int i = 0; i < dim; i ++) {
			max_number[i][x] = max(max_number[i][x], max_number[i][rc[x]]);
			min_number[i][x] = min(min_number[i][x], min_number[i][rc[x]]);
		}
	}
}//维护x子树的矩形。
```

  
在定义了以上的必需函数之后，可以进行建树。在建树时，每次递归建树需要根据不同的维度进行划分。因此考虑采用`kd % m`的方式，按照顺序依次采用各个维度进行划分即可。同时在建树过程中需要时刻维护结点对应的超矩形的信息。由上可得建树函数如下：  

```cpp
int build(int l, int r, int kd) {
	if(l > r) return 0;
	if(l == r) {
		maintain(l);
		return l;
	}
	int mid = (l + r) >> 1;
	kth_element_with_dim(mid, l, r, kd % dim);
	lc[mid] = build(l, mid - 1, kd + 1);
	rc[mid] = build(mid + 1, r, kd + 1);
	maintain(mid);
	return mid; 
}//建树
```

  
建树完毕后需要实现查询功能。若是每次查询都暴力枚举树中的每一个节点，时间复杂度为$O(n)$，因此需要进行剪枝。我们首先可以维护每次需要查询的向量到序号为$x$的结点对应的超矩形的距离：  

```cpp
long long distance_to_square(int x, Node y) {
    if(x == 0) return INF;
	long long res = 0;
	for(int i = 0; i < dim; i ++) {
		if(max_number[i][x] < y.num[i]) {
			res += 1ll * (y.num[i] - max_number[i][x]) * (y.num[i] - max_number[i][x]);
		}
		if(min_number[i][x] > y.num[i]) {
			res += 1ll * (min_number[i][x] - y.num[i]) * (min_number[i][x] - y.num[i]);
		}
	}
	return res;
}//获取给定点y到结点x对应矩形的距离
```

  
之后在查询时，首先对$x$结点和目标向量之间的距离与答案的全局变量取最小值，之后比较目标向量与$x$结点左右儿子对应超矩形之间的距离，再根据大小关系依次向两侧递归即可。实现代码如下：  

```cpp
void query(int x, Node tar) {
	if(x == 0) return;
	ans = min(ans, distance(x, tar));
	long long dis1 = distance_to_square(lc[x], tar);
	long long dis2 = distance_to_square(rc[x], tar);
	if(dis1 < dis2) {
		if(dis1 < ans) {
			query(lc[x], tar);
		}
		if(dis2 < ans) {
			query(rc[x], tar);
		}
	}
	else {
		if(dis2 < ans) {
			query(rc[x], tar);
		}
		if(dis1 < ans) {
			query(lc[x], tar);
		}
	}
}//查询距离
```

  
在最终实现时，我们通过`build(1, n, 0)`建立kd树并获取整棵树的根节点`root`，最后每次查询时，先将全局变量`ans`设置为给定的上界`INF = 1ll << 62`，之后通过`query(root, temp)`即可（`temp`为每次查询给出的向量）。


## 四、实现中值得注意的细节 {#四、实现中值得注意的细节}


1. 根据本题的数据范围，最终的结果（距离的平方）可能超过`int`数据范围，因此相关变量以及函数返回值需要使用`long long`数据类型进行存储。

2. 在输入给定的`n`个向量时，可以令数组下标从$1$开始进行存储，这样子可以在`point`数组中预留出首位用于处理特殊情况。例如上述的`query`函数中`if(x == 0) return;`一行就是利用的这一便利。



## 五、时间与空间复杂度分析 {#五、时间与空间复杂度分析}


1. 在本题中，主要的空间使用是用于存储给出的$n$个$d$维向量的每一维的数据信息，则空间复杂度为$O(dn)$。

2. 在本题中，实现`kth_element`算法的时间复杂度为$O(n)$，建树时每次根据中位数划分，则建立kd树的时间复杂度为$O(n\log{n})$。每次查询的时间复杂度为$O(\log{n})$，则总时间复杂度为$O((n+q)\log{n})$。
