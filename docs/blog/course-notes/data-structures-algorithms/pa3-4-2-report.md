---
id: pa3-4-2-report
title: PA3-4-2 Report
date: '2022-10-28'
updated: '2023-01-07'
description: 使用动态开点线段树处理大区间的更新与求和。
tags:
- DSA解题报告
---

## 一、题目大意 {#一、题目大意}


给定一个初始元素均为$0$的长度为$n$的区间，对区间进行$m$次以下操作：  
（1）修改：将某个子区间中所有元素的值增加$1$。  
（2）查询：查询某个子区间中所有元素的和。  
其中$1 \leq n < 2^{31}$，$1 \leq m \leq 200000$。


## 二、算法分析 {#二、算法分析}


本题是一道经典的利用线段树解决的算法题，因为线段树可以高效地支持在线段上进行区间修改和区间查询的操作。

若是采用数组模拟线段树的方法，考虑空间复杂度，最好的情况即是不断二分区间形成的线段树为完全二叉树，此时树中一共有$2n-1$个结点，需要的数组大小为$2n$；最坏的情况下，线段树的叶子结点一层中只有两个结点，但需要多进行一次二分开辟空间，需要的数组大小为$4n$。本题中，初始区间的长度$n$范围很大，使用数组模拟线段树会造成空间超限，因此采用动态加点的方法构造线段树，可以减少所需要使用的内存空间。


## 三、代码实现 {#三、代码实现}


为了实现线段树，我定义了一个`SegTree`类，将线段树的建立以及修改、查询等功能函数进行封装。该`SegTree`类的`private`成员中定义了如下的结构体`Node`，用来定义线段树中的每个结点。  

```cpp
struct Node{
	Node() : left(nullptr), right(nullptr), sum(0), tag(0) {}
	long long sum;
	long tag;
	Node *left;
	Node *right;
};
```

  
其中，`sum`表示这个结点代表的区间的元素和，`tag`为记录区间修改信息的懒惰标记，`*left`与`*right`为结构体指针，分别代表该结点的左右子结点，构造函数`Node()`将结点初始化为空。

`public`成员中，首先新建了一个结点`root`，表示整棵线段树的根结点，接着定义了`SegTree`类的构造函数与析构函数。  

```cpp
Node *root;
SegTree() { root = new Node(); }
~SegTree() {}
```


接下来便是线段树功能函数的实现。首先，我们需要实现对当前结点`curNode`的更新功能，为此实现`pushUp`函数，传入当前结点代表的区间的长度`len`，结合当前结点的懒惰标记实现对区间元素和的修改。同时需要检查左右子结点是否为空，若不为空，则也要加上左右子结点对应的区间元素和。  

```cpp
void pushUp(Node *curNode, int len) {
	curNode->sum = len * curNode -> tag;
	if(curNode->left != nullptr)
		curNode->sum += curNode->left->sum;
	if(curNode->right != nullptr)
		curNode->sum += curNode->right->sum;
}
```


接下来实现线段树对区间的修改功能。为此我们定义`upDate`函数，传入当前区间的左右下标，需要修改的区间的左右下标，以及对区间元素的修改值。若当前结点为空，则新增结点。若当前区间被所需要修改的区间所完全覆盖，则直接进行和的修改以及懒惰标记的修改：  

```cpp
if (upDateLeft <= curLeft && upDateRight >= curRight) {
	curNode->sum += addVal * (curRight - curLeft + 1);
	curNode->tag += addVal;
	return;
}
```

  
否则二分当前区间，向两侧递归调用：  

```cpp
int mid = (curLeft + curRight) / 2;
if (upDateLeft <= mid) {
	upDate(curNode->left, curLeft, mid, upDateLeft, upDateRight, addVal);
}
if (upDateRight > mid) {
	upDate(curNode->right, mid + 1, curRight, upDateLeft, upDateRight, addVal);
}
```

  
修改完成后，需要调用`pushUp`函数进行结点信息的更新。

接下来实现线段树查询区间元素和的功能。为此我们定义`query`函数，传入当前区间的左右下标，需要查询的区间的左右下标。若当前结点为空，则返回$0$。若当前区间被所需要查询的区间完全覆盖，则直接返回对应的元素和：  

```cpp
if (queryLeft <= curLeft && queryRight >= curRight) {
	return curNode->sum;
}
```

  
否则，记录当前区间与需查询区间的交的长度，先更新这一部分区间对当前区间对应的元素和的贡献，之后二分区间，向两侧递归调用，最后返回当前区间和即可：  

```cpp
int curSum = curNode->tag*(min(curRight,queryRight)-max(curLeft,queryLeft)+1);
int mid = (curLeft + curRight) / 2;
if (queryLeft <= mid) {
	curSum += query(curNode->left, curLeft, mid, queryLeft, queryRight);
}
if (queryRight > mid) {
	curSum += query(curNode->right, mid + 1, curRight, queryLeft, queryRight);
}
return curSum;
```



## 四、实现中值得注意的细节 {#四、实现中值得注意的细节}


1. 最终结果很大，需要用`long long`类型存储。

2. 一开始实现时，我还定义了一个`pushDown`下放函数，用于将当前结点的懒惰标记下放到子结点，以记录修改信息。在这一过程中，若是子结点为空，我进行了`new`操作，这一操作带来了许多不必要的空间开销，也即新建了很多没用到的空结点，造成Memory Limit Exceeded。于是采用懒惰标记永久化的办法，不需要定义下放函数，更新时遇到空结点，则新建；查询时对于空结点，则返回$0$，否则将懒惰标记记录的修改信息先行提取出来，也即代码中`int curSum = curNode->tag*(min(curRight,queryRight)-max(curLeft,queryLeft)+1);`这一行。这样大大减小了代码所需的空间开销。



## 五、时间与空间复杂度分析 {#五、时间与空间复杂度分析}


1. 时间复杂度分析：本题中，基于线段树的实现，对区间的修改和查询操作的时间复杂度均为$O(\log{n})$，则总时间复杂度为$O(m\log{n})$。

2. 空间复杂度分析：设$m$次操作中修改区间的操作次数为$T$，则每次修改操作所需要的空间复杂度均为$O(\log{n})$，则总空间复杂度为$O(T\log{n})$。
