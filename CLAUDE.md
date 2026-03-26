# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

《流放之路》(Path of Exile) 通货套利计算器。分析混沌石、神圣石与各种通货物品之间的套利机会。

## Core Architecture

### Module Structure

- **arbitrage.py** - 套利计算核心引擎
  - `ItemInfo`: 物品信息数据类 (混沌价格、神圣价格、手续费)
  - `CurrencyInfo`: 通货信息数据类 (神圣石汇率)
  - `TradePath`: 套利路径数据类 (包含收益计算)
  - `ArbitrageCalculator`: 计算器类，支持JSON数据加载和套利分析

- **ocr.py** - OCR模块，使用PaddleOCR从游戏截图中识别文本

### Arbitrage Logic

三步套利循环: **混沌 → 物品 → 神圣 → 混沌**

收益计算:
- 物品数量 = 混沌 / 物品混沌价格
- 神圣数量 = 物品数量 × 物品神圣价格
- 最终混沌 = 神圣数量 × 神圣混沌价格
- 混沌收益 = 最终混沌 - 起始混沌

手续费为独立的金币货币，每次交易消耗固定金币。

**核心排序指标**: 每金币获利 = 混沌收益 / 总手续费

### Data Format

price.json 数据格式:
```json
{
    "div": {
        "chaos": 360,
        "divs": 1,
        "golds": 500
    },
    "物品名": {
        "chaos": 混沌价格,
        "divs": 神圣价格,
        "golds": 手续费
    }
}
```

## Commands

```bash
# 安装依赖
pip install -r requirements.txt

# 运行套利计算
python arbitrage.py

# 运行OCR测试
python ocr.py
```

## Dependencies

- PaddlePaddle 2.6.2
- PaddleOCR 2.7.3
- OpenCV 4.5.5.64
- Python 3.11