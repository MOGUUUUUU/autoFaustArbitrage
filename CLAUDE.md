# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

《流放之路》(Path of Exile) 通货币场套利工具。自动扫描价格、计算套利机会。

## Module Structure

### arbitrage.py - 套利计算引擎
- `ItemInfo`: 物品信息 (混沌价格、神圣价格、手续费)
- `CurrencyInfo`: 神圣石汇率信息
- `TradePath`: 套利路径结果
- `ArbitrageCalculator`: 计算器，加载 JSON 并计算最佳套利

### faust.py - 价格扫描器
- `FaustPriceScanner`: 自动扫描游戏内通货价格
  - `scan_divine_price()`: 扫描神圣石混沌价格
  - `scan_item(item_name, gold_fee)`: 扫描单个物品价格
  - `scan_all(items)`: 批量扫描物品列表
  - `save_to_json()`: 保存为 price.json 格式

### ocr.py - OCR 文本识别
- 使用 PaddleOCR 从游戏截图识别文本

## Arbitrage Logic

三步套利: **混沌 → 物品 → 神圣 → 混沌**

```
物品数量 = 混沌 / 物品混沌价格
神圣数量 = 物品数量 × 物品神圣价格
最终混沌 = 神圣数量 × 神圣混沌价格
混沌收益 = 最终混沌 - 起始混沌
每金币获利 = 混沌收益 / 总手续费
```

## Data Format

price.json:
```json
{
    "div": {"chaos": 360, "divs": 1, "golds": 500},
    "物品名": {"chaos": 混沌价格, "divs": 神圣价格, "golds": 手续费}
}
```

## Commands

```bash
pip install -r requirements.txt

python faust.py      # 扫描价格生成 price.json
python arbitrage.py  # 计算套利机会
python ocr.py        # OCR 测试
```

## Dependencies

- PaddlePaddle 2.6.2
- PaddleOCR 2.7.3
- OpenCV 4.5.5.64
- PyAutoGUI / Pyperclip
- Python 3.11