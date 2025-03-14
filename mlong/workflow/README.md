# Workflow

通过配置文件来定义工作流，工作流是一系列任务的集合，每个任务都是一个独立的函数，任务之间可以通过消息队列来通信。
工作流的配置文件是一个YAML文件，它包含了工作流的名称、任务的定义、任务之间的依赖关系、任务的执行顺序等信息。下面是一个简单的工作流配置文件的例子：
```
name: my_workflow
workflow:
  - name: task1
    task: python task1.py
    depends_on: []
  - name: task2
    task: python task2.py
    depends_on:
      - task1
  - name: task3
    task: python task3.py
    depends_on:
      - task1
      - task2
```
