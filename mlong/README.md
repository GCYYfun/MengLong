# Model

封装了一些常用的模型，包括：
    openai:
        - GPT4
    anthropic:
        - Claude 3.5
    aws:
        - Claude 3.5
        - Nova Pro

## Usage

```python

modelconfig = {
    'openai': {
        'GPT4': {
            'model_name': 'openai',
            'model_type': 'GPT4',
            'model_path': 'openai/GPT4',
            'tokenizer_path': 'openai/GPT4',
            'model_config': 'openai/GPT4',
            'tokenizer_config': 'openai/GPT4',
            'model': None,
            'tokenizer': None
        }
    }
}

model = Model(modelid='openai.GPT4', modelconfig=modelconfig)


```

## Model Map

```python
```



# Agentic System

## Architecture

## Sub Module

## Task Manager (Monolithic)
    - Task Manager
    - Task
    - Task Queue
    - Task Scheduler
    - Task Monitor
    - Task Executor
    - Task Logger
