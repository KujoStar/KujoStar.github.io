---
id: pa2-2-report
title: PA2-2 Report
date: '2023-01-26'
updated: '2023-01-26'
description: 通过多项式运算与栈求值，实现表达式展开。
tags:
- DSA解题报告
---

## 一、题目大意 {#一、题目大意}


本题输入为一串长度为$n$的字符串，表示一个含有加法、减法、乘法、乘方以及括号运算的多项式$f(x)$。我们要做的是将多项式展开为如下的标准形式：

并按照次数从高到低的顺序输出每一项的系数$a_i$对1000000007取模的值。

题目数据保证$0 < n \leq 1000000$，计算过程中涉及的乘方运算最多不超过$4$次乘方，涉及的多项式的最高次数不超过$64$。


## 二、算法分析 {#二、算法分析}


我们首先考虑不含字母$x$，只有数字的表达式的求值问题，容易想到课上所讲的中缀表达式求值的方法。于是可以类推到本题。在本题中，我们使用栈1存储所有需要操作的多项式，称为操作数栈；使用栈2存储字符串中的运算符和左右括号，称为操作符栈。这样我们就可以将中缀表达式求值的算法推广到对多项式的化简问题中。


## 三、代码实现 {#三、代码实现}


为了存储待操作的多项式，采用定义结构体的方式来存储结构体：  

```cpp
struct poly {
    int max_deg;
    int num[65];
};
```

  
结构体中定义了一个整型变量`max_deg`，表示存储的多项式的最高次数。由于计算过程中涉及的多项式最高次数不超过64，则定义一个65位的整型数组，其中第$i$位存储$x^i$项的系数。接着为了方便进行多项式之间的运算，对+、-、\*、^四个运算符进行了结构体内重载。

在对加减号的重载中，我们令结果的最高次数为两个被操作多项式的最高次数中较大者，即接着对两个`num`数组进行按位加或减即可得到结果多项式的`num`数组。  

```cpp
poly operator+(const poly &other) {//此处以对+号的重载为例
        this->max_deg = max(this->max_deg, other.max_deg);
        for(int i = 0; i <= this->max_deg; i ++){
            this->num[i] = (this->num[i] + other.num[i]) % mod;//处理模数
        }
        return *this;
    }
```


在对乘号的重载中，我们令结果的最高次数为两个被操作多项式的最高次数相加，然后在计算系数的时候模拟竖式运算即可。  

```cpp
poly operator*(const poly &other) {
        long long temp[65] = {0};
        for(int i = 0; i <= this->max_deg; i ++) {
            for(int j = 0;j <= other.max_deg; j ++) {
                temp[i + j] += 1ll * this->num[i] * other.num[j] % mod;
            }
        }
        this->max_deg = this->max_deg + other.max_deg;
        for(int i = 0; i < 65; i ++) {
            this->num[i] = temp[i] % mod;//处理模数
        }
        return *this;
    }
```


在对乘方的重载中，我们额外定义一个多项式结构体temp来存储原有的底数多项式，定义ans用来保存最后的答案，然后获取指数，调用已经重载完成的\*运算符即可。  

```cpp
poly operator^(const poly &other) {
        int times = other.num[0];
        poly temp, ans;
        temp.max_deg = this->max_deg;
        ans.max_deg = this->max_deg;
        for(int i = 0; i < 65; i ++) {
            temp.num[i] = this->num[i];
            ans.num[i] = this->num[i];
        }
        for(int i = 0; i < times - 1; i ++) {
            ans = ans * temp;
        }
        this->max_deg = ans.max_deg;
        for(int i = 0; i < 65; i ++) {
            this->num[i] = ans.num[i];
        }
        return *this;
    }
```

  
所有的重载过程中，都需要适当处理模数问题。

重载完成后，下一步是对输入字符串的处理。在本题中，为了便于处理，将数字和$x$字母分开，各自分别算作一个多项式，也即$x+1$中含有$x$和$1$两个多项式。结合题面中省略乘号的规则，我们需要在输入字符串的相应位置补上乘号，从而可以进行中缀表达式求值。事实上，若字符串中第$i$个字符为数字或者字符$x$或者右括号，第$i + 1$个字符为数字或者字符$x$或者左括号，且这两个字符不同时为数字，则之间需要补充乘号。代码实现如下：  

```cpp
string input;
cin>>input;
int len = input.size();
for(int i = 0; i < len - 1; i ++) {
    final_input.append(1, input[i]);
    if((is_num(input[i]) || input[i] == 'x' || input[i] == ')') && 
    (is_num(input[i + 1]) || input[i + 1] == 'x' || input[i + 1] == '(') &&
    !(is_num(input[i]) && is_num(input[i + 1]))) {
        final_input.append(1, '*');
    }
}
final_input.append(1, input[len - 1]);
```


处理完字符串之后，便是中缀表达式求值环节。由于本课程的OJ系统禁止直接使用STL库中的stack，于是采用手动实现栈的方式。每个栈采用结构体的方式实现，结构体成员为一个对应数据类型的数组`data`，以及一个整型变量`top`代表栈顶指针。结构体中定义了成员函数`pop()`，`push()`，`top()`，利用`top`的增减与`data`数组的修改，全方位模拟实际栈的功能。  

```cpp
struct stack_ops {//以操作符栈为例
    char data[N];//char类型的数据域
    int top;//栈顶指针
    stack_ops() {
        top = -1;
    }//初始化构造函数
    bool push(char other) {
        if(top + 1 < N) {
            top ++;
            data[top] = other;
            return true;
        }
        return false;
    }//入栈函数
    bool pop() {
        if(top >= 0) {
            top --;
            return true;
        }
        return false;
    }//出栈函数
    char top_n() {
        if(top >= 0) {
            return data[top];
        }
        return 0;
    }//获取栈顶元素
};
```

  
解决了栈的模拟问题之后，便是计算环节。为了方便实现，首先将运算符之间的优先级关系打成一张表，需要时直接访问即可；同时为了方便检查运算是否结束，我们引入符号$$$作为字符串的起始符和终止符。于是操作符优先级表如下：  

```cpp
const char op_priority[7][8] = {
    ">><<<>>",
    ">><<<>>",
    ">>><<>>",
    ">>>><>>",
    "<<<<<= ",
    "       ",
    "<<<<< <"
};//[已有的栈顶运算符][即将进栈的运算符]优先级关系，顺序为"+-*^()$"
```


下面定义`calculate()`函数进行运算，首先在字符串的前后各加上起始符和终止符，接着从前到后依次扫描每个字符。  
若遇到数字，则定义一个最高次数为0，`num`数组只有`num[0]`有值的多项式，进入操作数栈。  

```cpp
if(is_num(s[i])) {//传入的字符串为s
        poly temp;
        temp.clear();
        temp.num[0] = int(s[i]) - 48;
        i ++;
        while(i < len && is_num(s[i])) {
            temp.num[0] = (10ll * temp.num[0] + (int(s[i]) - 48)) % mod;
            i ++;
        }//检查是否数字不止一位
        opnd.push(temp);
    }
```

  
若遇到$x$，则定义一个最高次数为1，`num`数组只有`num[1] = 1`的多项式，进入操作数栈。  

```cpp
else if (s[i] == 'x') {
    poly temp;
    temp.clear();
    temp.max_deg = 1;
    temp.num[1] = 1;
    opnd.push(temp);
    i ++;
}
```

  
若遇到操作符，则比较当前操作符与栈顶操作符的优先级。若优先级为<，则推迟计算，当前操作符入栈；若优先级为>，则连续两次取出操作数栈中的栈顶元素，根据操作符栈顶运算符进行计算，结果进入操作数栈；若优先级为=，则说明有一对括号匹配成功，此时操作符栈栈顶为左括号，则将左括号弹出，括号内计算结束。当扫描到最后一位，处理结束，则操作数栈栈顶元素即为整理完毕的多项式，并作为`calculate()`函数的返回值。  

```cpp
switch (op_priority[top_pos][in_pos]) {
    case '<':
        optr.push(s[i]);
        i ++;
        break;
    case '>':{
        char op = optr.top_n();
        optr.pop();
        if(op == '+') {
            poly temp2 = opnd.top_n();
            opnd.pop();
            poly temp1 = opnd.top_n();
            opnd.pop();
            poly answer = temp1 + temp2;
            opnd.push(answer);
        }
        ......//类似操作，根据栈顶运算符决定
        break;  
    case '=':
        optr.pop();
        i ++;
        break;
```


在最终输出的时候，注意按照从高位到地位的顺序输出即可。  

```cpp
poly ans = calculate(final_input);
    for(int i = 0; i <= ans.max_deg; i ++) {
        cout << ans.num[ans.max_deg - i] << " ";
    }
```



## 四、实现中值得注意的细节 {#四、实现中值得注意的细节}


1. 在重载运算符时，需要注意出现最高次项对应的系数为0的情况，例如计算过程中出现了`x-x`这样的运算。于是我们额外定义一个名为`process`的成员函数，每当出现`num[max_deg] = 0`的情况时，则执行`max_deg --`，直到`num[max_deg] != 0`或者`max_deg = 0`。


    ```cpp
    void process() {
            while(this->num[max_deg] == 0 && max_deg > 0) {
                max_deg --;
            }
        }
    ```


2. 在重载运算符时，为了节省时间，循环的终止数设置为多项式的`max_deg`，而不是每次循环都要遍历数组的65位。例如在运算$x+x$时，直接循环两次即可，相比循环65次，在运算次数很多时，可以大量节省时间。

3. 在涉及到数字之间的乘法的操作（重载\*运算符以及处理字符串遇到不止一位的数字）时，由于运算中的结果可能超过`int`可能表示的范围，则采用如下的方式（乘以`1ll`）将结果转为`long long`类型。

    ```cpp
    temp[i + j] += 1ll * this->num[i] * other.num[j] % mod;
    ```


4. 在初次提交时，由于题中设定输入字符串的长度不超过1000000，于是我设置`const int N = 1000005`，将操作数栈和操作符栈中的数据域大小都设置为`N`，提交之后造成了Memory Limit Error。经过分析，我发现操作数栈不需要申请这么多空间。事实上，在最劣的情况下，每三位字符中都至少有一个操作符，例如以下的字符串`2x+2x+2x+2x+...`，此时`2`，`x`均为操作数，`+`为操作符。其他情况下，数字位数变多，则必然操作数总数会减少。则操作数的总数最多不会超过`2 * N / 3`，于是设置`const int N2 = 2 * N / 3`，将操作数栈中数据域的大小设置为`N2`，解决了内存超限的问题。

5. 在给输入字符串补充乘号的时候，没有采用$O(n)$的`insert()`等方法，而是采用了新开字符串，并且依次`append()`的方法，将每次补乘号的时间缩短到了$O(1)$。



## 五、时间与空间复杂度分析 {#五、时间与空间复杂度分析}


1. 时间复杂度分析：在本题中，对字符串的操作的复杂度整体是$O(n)$的，而在运算数运算过程中，单次运算最劣复杂度为$O(m^2)$，则本题算法理论时间复杂度为$O(m^2 n)$。

2. 空间复杂度分析：在本题中，主要的空间开销是在定义操作符栈和操作数栈的过程，则本题算法理论空间复杂度为$O(mn)$。
