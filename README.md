# 桌面便利贴 (Sticky Note)

一个轻便的桌面日程便利贴应用，支持窗口置顶、数据持久化、开机启动等功能。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 功能特性

- 📌 **窗口置顶** - 固定在桌面右上角，不碍事
- 🎨 **便利贴风格** - 黄色主题，简洁美观
- ✏️ **双击编辑** - 时间/事项可编辑
- ✓ **完成情况** - 单击切换 √ / × / -
- 💾 **自动保存** - 数据实时保存到 JSON
- 🔄 **一键刷新** - 清空所有事项
- 🚀 **开机启动** - 支持设置开机自动运行
- 📦 **单文件运行** - 打包成 exe，无需安装 Python

## 效果预览

| 界面 | 说明 |
|------|------|
| 序号 | 自动编号 1-10 |
| 时间 | 下拉选择 (00:00-23:30) |
| 事项 | 直接输入 |
| 完成情况 | 单击切换 √ / × / - |

## 使用方法

### 方式一：直接运行 exe（推荐）
1. 下载 `dist/桌面便利贴.exe`
2. 双击运行即可

### 方式二：Python 运行
1. 确保已安装 Python 3.8+
2. 运行 `python sticky_schedule.py`

## 右键菜单功能

| 功能 | 说明 |
|------|------|
| 新增一行 | 添加新事项 |
| 删除选中 | 删除选中行 |
| 一键刷新 | 清空所有事项 |
| 开机启动 | 切换开机启动状态 |
| 退出 | 关闭程序 |

## 文件说明

| 文件 | 说明 |
|------|------|
| `sticky_schedule.py` | 源代码 |
| `桌面便利贴.exe` | 打包后的可执行文件 |
| `schedule_data.json` | 数据存储文件 |
| `sticky.ico` | 程序图标 |

## 打包方法

如需重新打包：
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "桌面便利贴" --icon=sticky.ico sticky_schedule.py
```

## 技术栈

- Python 3.8+
- tkinter / ttk
- PyInstaller

## License

MIT License
