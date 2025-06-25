# Rich Tool 新功能总结

## 新增功能

### 1. print_generate()

**功能描述**: 展示生成器或可迭代对象的内容，支持进度显示

**参数**:
- `generator`: 可迭代对象或生成器
- `title`: 可选标题
- `show_progress`: 是否显示进度 (默认 True)
- `style`: 文本样式 (默认 "cyan")

**返回值**: 生成器产生的所有项目列表

**使用场景**:
- 文件批处理
- 数据流处理
- 任务序列执行
- 步骤展示

**示例**:
```python
# 处理文件列表
files = ["file1.txt", "file2.py", "file3.md"]
results = print_generate(files, title="处理文件", style="green")

# 处理生成器
data_gen = (f"数据 {i}" for i in range(10))
print_generate(data_gen, title="数据处理", show_progress=True)

# 简洁模式
steps = ["初始化", "连接", "启动"]
print_generate(steps, show_progress=False, style="yellow")
```

### 2. print_progress()

**功能描述**: 显示多任务进度跟踪和可视化

**参数**:
- `tasks`: 任务列表，每个任务应包含 'name', 'total', 'completed' 字段
- `title`: 可选标题
- `show_details`: 是否显示详细信息 (默认 True)

**任务字典格式**:
```python
{
    "name": "任务名称",
    "total": 总数量,
    "completed": 已完成数量
}
```

**使用场景**:
- 多任务监控
- 项目进度跟踪
- 安装进度显示
- 批处理状态

**示例**:
```python
# 基本用法
tasks = [
    {"name": "下载文件", "total": 100, "completed": 75},
    {"name": "安装依赖", "total": 50, "completed": 30},
    {"name": "配置环境", "total": 20, "completed": 20},
]
print_progress(tasks, title="安装进度", show_details=True)

# 简化显示
print_progress(tasks, show_details=False)
```

## 特性说明

### print_generate 特性

1. **自动进度检测**: 
   - 有长度的对象显示进度条
   - 无长度的生成器显示计数

2. **灵活样式控制**:
   - 支持自定义颜色样式
   - 可选择显示或隐藏进度

3. **完整性保证**:
   - 返回所有处理的项目
   - 显示最终统计信息

### print_progress 特性

1. **可视化进度条**:
   - 使用 Unicode 字符绘制进度条
   - 颜色编码状态（完成/进行中/等待）

2. **详细统计**:
   - 显示总体进度统计
   - 任务完成状态汇总

3. **灵活显示模式**:
   - 详细模式：包含统计信息
   - 简洁模式：仅显示进度表格

## 更新的文件

### 核心文件
- `src/menglong/utils/log/rich_tool.py`: 添加新功能实现
- `src/menglong/utils/log/__init__.py`: 更新导出列表

### 演示文件
- `examples/demo/rich_tool_demo_standalone.py`: 添加新功能演示
- `test_new_features.py`: 新功能专项测试

### 文档文件
- `examples/demo/README.md`: 更新使用说明

## 兼容性

- ✅ 向后兼容：不影响现有功能
- ✅ 统一接口：遵循现有命名和参数约定
- ✅ 样式一致：使用相同的颜色和布局风格
- ✅ 无图标设计：保持简洁的视觉风格

## 测试验证

所有新功能都经过了完整测试：

1. **单元测试**: 各功能独立测试
2. **集成测试**: 功能组合使用测试
3. **场景测试**: 真实使用场景模拟
4. **边界测试**: 空数据、异常情况处理

## 使用建议

1. **print_generate**: 适合需要展示处理过程的场景
2. **print_progress**: 适合需要监控多任务状态的场景
3. **组合使用**: 可以结合使用来展示完整的工作流程

这些新功能进一步增强了 Rich Tool 的实用性和表现力，为用户提供了更丰富的数据展示和进度跟踪选项。
