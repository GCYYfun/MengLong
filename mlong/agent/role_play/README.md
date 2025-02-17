
# Role Play

对话模式
单Agent为体
以多Agent为用

# Single Role Play with Human

单 agent 与 human 的对话模拟。


# Multi-Agent Role Play (or with Human)

多个角色之间的对话模拟。

区分 `两人` 和 `多人` 的概念。

两人的对话模拟，可以看作是一种 `对话`，只不过是由两个角色来进行。
由human 与 agent 模式，转变为，agent 与 agent 模式。

对话的模式，一般是由 `一问一答` 模式组成，这受限于目前模型训练的数据集。大部分数据分布是这样的。

所以双人对话主动发起对话的是 human ，而被动回答的是 agent。对话定义，话题发起者是主动方（active），话题回答者是被动方（passive）。

init_two(a,c)  # a 主动，c 被动

多人对话模拟，可以看作是一种 `讨论`，只不过是由多个角色来进行。

讨论规则很多，可以是自由讨论，也可以是有主题讨论。可以是有主持人，也可以是自由讨论。

所以对于多人模式，要有规则的定义，这样才能更好的进行讨论。对应也是不同形式的实现

init_multi(a,b,c,d)  # a 主持人，b,c,d 参与者


topic 定义
    $ task background description
    $ role aim 
    $ notice
    $ end condition


例子：
    $ task background description 两人相遇互相打招呼，自我介绍，然后聊天
    $ role aim 互相了解对方，建立友好关系
    $ notice 互相尊重，不要说伤害对方的话
    $ end condition 任意一方可以主动结束对话
