---
id: pa1-2-report
title: PA1-2 Report
date: '2023-01-20'
updated: '2023-01-20'
tags:
- DSA解题报告
---

## 一、题目大意 {#一、题目大意}


给定$n$条端点在坐标轴正半轴上，且坐标值递增的线段，给定坐标平面上一个固定点$P$，查询有多少条线段在$P$的左边。


## 二、算法分析及代码实现 {#二、算法分析及代码实现}


由于输入的线段端点坐标是无序的，因此需要先对坐标进行排序，为此使用快速排序算法，时间复杂度$O(n\log{n})$。  

```cpp
void quicksort(long long num[], int left, int right) {
    if(left < right) {
        int i = left, j = right, temp = num[left];
        while(i < j) {
            while(i < j && num[j] >= temp) {
                j --;
            }
            if(i < j) {
                num[i ++] = num[j];
            }
            while(i < j && num[i] < temp) {
                i ++;
            }
            if(i < j) {
                num[j --] = num[i];
            } 
        }
        num[i] = temp;
        quicksort(num, left, i -1);
        quicksort(num, i + 1, right);
    }
    else {
        return;
    }
}
```


接着，我们要判断点与线段的位置关系，自然想到用向量叉积的大小来判断。设线段为$PQ$，点为$R$，按逆时针方向构造向量$\overrightarrow{PQ}, \overrightarrow{QR}$，计算$\overrightarrow{PQ} \times \overrightarrow{QR}$的值，若值大于等于0，则点在线段上或在线段右侧，则点与原点O的连线与该线段有交点；反之就没有交点。由此可以定义函数$check$来判断是否有交点。  

```cpp
int check(PointInfo point, long long num_x, long long num_y) {
    long long area = num_x * point.y + num_y * point.x - num_x * num_y;
    if(area >= 0) {
        return 1;
    }
    else {
        return 0;
    }
}
```


为了提高效率，由于线段的排列是有序的，则在计算交点个数的时候可以采用二分查找，快速找到最后一个有交点的线段的序号，则也就知道了交点的个数，时间复杂度$O(\log{n})$。  

```cpp
for(int i = 0; i < m; i ++) {
        int low = 0;
        int high = n;
        int mid = (low + high) / 2;
        while(low < high - 1) {
            if (check(point[i], num_x[mid], num_y[mid]) == 1){
                low = mid;
            }
            else {
                high = mid;
            }
            mid = (low + high) / 2;
        }
        if(low == 0 && check(point[i], num_x[0], num_y[0]) == 0) {
            printf("%d\n", low);
        }//此处当low=0时进行特判
        else {
            printf("%d\n", low + 1);
        }
    }
```



## 三、复杂度分析 {#三、复杂度分析}


本题算法的时间复杂度为$O(n\log{n})$，空间复杂度为$O(n)$。
