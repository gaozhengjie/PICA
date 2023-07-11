[**中文**](./README.md) | [**English**](./README_EN.md)

<p align="center" width="100%">
<a href="https://github.com/NEU-DataMining/Emo-LLM" target="_blank"><img src="logo.png" alt="EMO_LLM" style="width: 35%; min-width: 300px; display: block; margin: auto;"></a>
</p>

# PICA: A comprehensive language model with satisfying empathetical ability
## 模型介绍
开源多轮共情对话模型PICA（喜鹊）。

权重下载: [https://huggingface.co/NEUDM/PICA-V1](https://huggingface.co/NEUDM/PICA-V1)
## 更新 

&#x1F5D3; **2023.7.11** 公布了由少量自建共情数据集（中文）精调得到的模型的权重(P-Tuning V2 weights)

## 案例分析

1️⃣ 对抽象问题咨询的测试

###### 用户：
> 我总是对自己的能力感到怀疑，做什么事情都会犹豫，然后失去最好的去做的机会，之后又非常懊悔，你说该怎么办？
###### PICA:
> 感到犹豫和拖延是很正常的事，特别是在面对重要决策时。首先，你可以尝试分解任务，将它们分解成为更小的步骤，这样可以帮助你更容易地完成任务。
###### 用户：
> 哦，我明白了，通过分解成更小的步骤，然后再努力去做，不要拖延，是吗？可是有时候，我会觉得就算做了也没有用，对自己未来不抱希望了，没有做事的动力，该怎么办呢？
###### PICA:
>有时候，我们可能会对自己没有动力而感到沮丧，但是请相信，你所做的每一个步骤都会为未来做好准备。同时，你可以寻找支持和鼓励的人，这样可以让你更有动力去完成任务。
###### 用户：
>谢谢你的帮助。当看到身边的人很优秀而自己比较落后，该怎么才能继续坚持努力，不要打乱自己的节奏呢？
###### PICA:
>每个人的人生轨迹不同，没有必要与人比较。重要的是，你能够实现自己的目标，而不是只是与他人的差距。记住，每个人都有自己的节奏和目标，你的努力也会得到回报

模型对情感能够准确识别，并给出积极的引导

2️⃣ 对具体问题咨询的测试

###### 用户：
>我现在处于高二的暑假，需要补课。我的妈妈要我同时参加家教和集体补课，我的爸爸说这样就没有整理复习的时间了，家教针对性强些，只参加家教课，老师说集体补课学习氛围更好，只需要集体补课就够了。我自己一点注意也没有，你说该怎么办？
###### PICA:
>我明白你的困惑和纠结。 在这种情况下，你可以考虑与你的妈妈和爸爸进行沟通，告诉他们你的困惑和需要调整的学习计划。你可以提出你希望专注于学习的内容，并提供一些具体的建议。同时，你也可以寻求其他学生或老师的帮助，获取更多的学习资源和支持。
###### 用户：
>其实我是很想两个都参加的，可是怕自己给家庭造成经济负担，然后还是没学好让父母失望。
###### PICA:
>这是一个很好的问题！你可以尝试与你的妈妈和爸爸讨论一下，看看他们是否能够理解你的困境，并提供一些解决方案。同时，你也可以考虑与同学或老师建立良好的合作关系，互相帮助和支持。这样，你可以更好地平衡学习和家庭的责任。
###### 用户：
>你能给我些鼓励，让我坚持自己的想法，并且为即将到来的高考好好拼搏一番吗？
###### PICA:
>当然可以！你已经迈出了第一步，相信自己能够实现目标。记住，成功需要坚持和努力。相信自己的能力，相信你所做出的决定，继续朝着自己的目标努力前进。相信自己，你一定能够取得好成绩！

## 项目贡献者
张逸群[@张逸群](https://github.com/ZhangYiqun018), 
## 引用
如果使用本项目的代码、数据或者模型，请引用本项目。
```
@misc{zhang2023PICA,
      title={多轮对话共情大模型PICA},
      author={Yiqun Zhang, Jingqing Zhang, Yongkang Liu, Chongyun Gao, Daling Wang, Shi Feng, Yifei Zhang},
      year={2023},
      month={7},
      version={1.0},
      url={https://github.com/NEU-DataMining/PICA}
}
```
