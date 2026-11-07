# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.

## 🧪 如何运行测试

本项目使用 `pytest` 进行单元测试和集成测试。

### 1. 运行所有测试
在终端中执行以下命令：
```bash
pytest

### 📊 查看测试覆盖率

本项目支持生成代码覆盖率报告，以评估测试的完整度。

**步骤如下：**

1. 安装覆盖率插件：
   ```bash
   pip install pytest-cov
2.运行测试并生成报告
   pytest --cov=app --cov-report=term