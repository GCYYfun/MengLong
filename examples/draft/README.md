# Rich Tool 使用说明

Rich Tool 是 MengLong 项目中的美观打印工具，提供丰富的文本格式化和数据展示功能。

## 特性

- ✅ **无图标设计**: 默认不使用图标，界面简洁
- ✅ **多种消息类型**: 支持 success, error, warning, info, debug, system, user, agent, tool
- ✅ **丰富的展示方式**: 表格、JSON、Markdown、树形结构、面板等
- ✅ **布局功能**: 居中、分隔线、头部、尾部
- ✅ **交互元素**: 进度条、状态指示器
- ✅ **灵活配置**: 支持时间戳、面板包装、自定义样式

## 快速开始

```python
from menglong.utils.log.rich_tool import *

# 基本消息
success("操作成功！")
error("发生错误")
warning("警告信息")
info("普通信息")

# 带选项的消息
success("成功", timestamp=True)
error("错误", panel=True, title="错误详情")

# 数据展示
data = [{"姓名": "张三", "年龄": 25}]
print_table(data, title="用户信息")

config = {"key": "value"}
print_json(config, title="配置")
```

## 主要功能

### 1. 消息类型

```python
success("成功消息")      # 绿色
error("错误消息")        # 红色  
warning("警告消息")      # 黄色
info("信息消息")         # 蓝色
debug("调试消息")        # 暗绿色
system("系统消息")       # 蓝色粗体
user("用户消息")         # 紫色
agent("智能体消息")      # 绿色粗体
tool("工具消息")         # 紫色
```

### 2. 数据展示

```python
# 表格
table_data = [
    {"姓名": "张三", "年龄": 25, "职业": "工程师"},
    {"姓名": "李四", "年龄": 30, "职业": "设计师"}
]
print_table(table_data, title="员工信息")

# JSON 数据
config = {"项目": "MengLong", "版本": "1.0.0"}
print_json(config, title="配置信息")

# 树形结构  
tree_data = {
    "根目录": {
        "子目录1": ["文件1.txt", "文件2.py"],
        "子目录2": {"嵌套": ["文件3.md"]}
    }
}
print_tree(tree_data, title="项目结构")
```

### 3. 布局和样式

```python
# 面板
print_panel("重要信息", title="通知", style="blue")

# 居中显示
print_center("标题文本", "bold bright_blue")

# 分隔线
print_rule("章节标题", "green")

# 头部和尾部
print_header("主标题", "副标题")
print_footer("完成")

# 分隔符
print_separator("=", 30, "blue")
```

### 4. 交互功能

```python
# 状态指示器
with print_status("处理中...") as status:
    # 处理任务
    status.update("正在保存...")

# 进度条演示
print_progress_demo()
```

### 5. 便捷函数

```python
# 字典和列表
print_dict({"key": "value"}, title="数据")
print_list(["item1", "item2"], title="列表")

# Markdown
markdown_text = "# 标题\n\n这是 **粗体** 文本"
print_markdown(markdown_text, title="文档")
```

## 消息选项

所有消息函数都支持以下选项：

- `timestamp=True`: 显示时间戳
- `panel=True`: 使用面板包装
- `title="标题"`: 添加标题

```python
success("成功", timestamp=True, panel=True, title="操作结果")
```

## 演示程序

运行完整的功能演示：

```bash
python examples/demo/rich_tool_demo.py
```

运行快速测试：

```bash
python test_rich_quick.py
```

## 设计理念

1. **简洁优先**: 不使用图标，界面简洁清晰
2. **功能丰富**: 提供多种展示方式和配置选项
3. **易于使用**: 直观的函数名和参数设计
4. **高度兼容**: 与原有代码保持兼容性

## API 参考

### 核心消息函数
- `success(message, **kwargs)` - 成功消息
- `error(message, **kwargs)` - 错误消息  
- `warning(message, **kwargs)` - 警告消息
- `info(message, **kwargs)` - 信息消息
- `debug(message, **kwargs)` - 调试消息
- `system(message, **kwargs)` - 系统消息
- `user(message, **kwargs)` - 用户消息
- `agent(message, **kwargs)` - 智能体消息
- `tool(message, **kwargs)` - 工具消息

### 数据展示函数
- `print_table(data, title, headers, show_header, show_lines)` - 打印表格
- `print_json(data, title, indent, sort_keys)` - 打印 JSON
- `print_markdown(markdown, title)` - 渲染 Markdown
- `print_tree(data, title, guide_style)` - 打印树形结构
- `print_dict(data, title)` - 打印字典
- `print_list(data, title)` - 打印列表

### 布局函数
- `print_panel(content, title, style, width, padding)` - 打印面板
- `print_center(content, style)` - 居中显示
- `print_rule(title, style)` - 打印分隔线
- `print_header(title, subtitle)` - 打印头部
- `print_footer(message)` - 打印尾部
- `print_separator(char, length, style)` - 打印分隔符

### 交互函数
- `print_status(message, spinner)` - 状态指示器
- `print_progress_demo()` - 进度条演示

## 兼容性

为了与现有代码兼容，保留了以下函数：
- `rich_print(message, msg_type, **kwargs)` - 映射到 `print_message`
- `rich_print_json(data, title, **kwargs)` - 映射到 `print_json`
