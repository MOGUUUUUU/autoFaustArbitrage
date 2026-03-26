"""
《流放之路》(Path of Exile) 通货套利计算模块

核心概念:
- 套利路径: A通货 -> 物品 -> B通货 -> A通货
- 手续费是独立的金币货币
- 收益 = 最终A通货数量 - 初始A通货数量
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ItemInfo:
    """物品信息"""
    name: str
    chaos: float    # 混沌价格
    divs: float     # 神圣价格
    golds: float    # 手续费(金币)


@dataclass
class CurrencyInfo:
    """通货信息"""
    chaos: float    # 混沌汇率
    divs: float     # 神圣汇率 (通常为1)
    golds: float    # 手续费(金币)


@dataclass
class TradePath:
    """套利路径"""
    item_name: str          # 物品名称
    start_chaos: float      # 起始混沌
    end_chaos: float        # 结束混沌
    end_divine: float       # 中间步骤神圣数量
    profit_chaos: float     # 混沌收益
    total_gold_fee: float   # 总手续费(金币)
    profit_per_gold: float  # 每金币获利
    steps: List[Dict]       # 交易步骤


class ArbitrageCalculator:
    """套利计算器 - 基于JSON数据"""

    def __init__(self):
        self.divine_info: Optional[CurrencyInfo] = None
        self.items: Dict[str, ItemInfo] = {}

    def load_from_json(self, filepath: str):
        """从JSON文件加载数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 加载神圣石信息
        if 'div' in data:
            div_data = data['div']
            self.divine_info = CurrencyInfo(
                chaos=div_data.get('chaos', 0),
                divs=div_data.get('divs', 1),
                golds=div_data.get('golds', 0)
            )

        # 加载物品信息 (排除'div')
        for key, value in data.items():
            if key != 'div':
                self.items[key] = ItemInfo(
                    name=key,
                    chaos=value.get('chaos', 0),
                    divs=value.get('divs', 0),
                    golds=value.get('golds', 0)
                )

    def load_from_dict(self, data: Dict):
        """从字典加载数据"""
        if 'div' in data:
            div_data = data['div']
            self.divine_info = CurrencyInfo(
                chaos=div_data.get('chaos', 0),
                divs=div_data.get('divs', 1),
                golds=div_data.get('golds', 0)
            )

        for key, value in data.items():
            if key != 'div':
                self.items[key] = ItemInfo(
                    name=key,
                    chaos=value.get('chaos', 0),
                    divs=value.get('divs', 0),
                    golds=value.get('golds', 0)
                )

    def calc_arbitrage(self, item_name: str, start_chaos: float = 1.0) -> Optional[TradePath]:
        """
        计算三步套利: 混沌 -> 物品 -> 神圣 -> 混沌

        Args:
            item_name: 物品名称
            start_chaos: 起始混沌数量

        Returns:
            TradePath 或 None(如果数据不完整)
        """
        if item_name not in self.items:
            return None
        if self.divine_info is None:
            return None

        item = self.items[item_name]
        divine = self.divine_info

        # 步骤1: 用混沌买入物品
        # 物品数量 = 混沌 / 物品混沌价格
        item_amount = start_chaos / item.chaos if item.chaos > 0 else 0
        gold_fee_1 = item.golds  # 买物品的手续费

        # 步骤2: 卖出物品获得神圣
        # 神圣数量 = 物品数量 × 物品神圣价格
        divine_amount = item_amount * item.divs
        gold_fee_2 = item.golds  # 卖物品的手续费

        # 步骤3: 神圣换回混沌
        # 最终混沌 = 神圣数量 × 神圣混沌价格
        end_chaos = divine_amount * divine.chaos
        gold_fee_3 = divine.golds  # 换混沌的手续费

        # 总收益
        profit_chaos = end_chaos - start_chaos
        total_gold = gold_fee_1 + gold_fee_2 + gold_fee_3

        # 每金币获利
        profit_per_gold = profit_chaos / total_gold if total_gold > 0 else 0

        return TradePath(
            item_name=item_name,
            start_chaos=start_chaos,
            end_chaos=end_chaos,
            end_divine=divine_amount,
            profit_chaos=profit_chaos,
            total_gold_fee=total_gold,
            profit_per_gold=profit_per_gold,
            steps=[
                {
                    "step": 1,
                    "action": f"用 {start_chaos:.2f} 混沌买入 {item_name}",
                    "result": f"获得 {item_amount:.4f} {item_name}",
                    "rate": f"1 {item_name} = {item.chaos:.2f} 混沌",
                    "gold_fee": gold_fee_1
                },
                {
                    "step": 2,
                    "action": f"卖出 {item_amount:.4f} {item_name}",
                    "result": f"获得 {divine_amount:.4f} 神圣",
                    "rate": f"1 {item_name} = {item.divs:.4f} 神圣",
                    "gold_fee": gold_fee_2
                },
                {
                    "step": 3,
                    "action": f"用 {divine_amount:.4f} 神圣换混沌",
                    "result": f"获得 {end_chaos:.2f} 混沌",
                    "rate": f"1 神圣 = {divine.chaos:.2f} 混沌",
                    "gold_fee": gold_fee_3
                }
            ]
        )

    def find_all_opportunities(self, start_chaos: float = 1.0, min_profit: float = 0) -> List[TradePath]:
        """
        查找所有有收益的套利机会

        Args:
            start_chaos: 起始混沌数量
            min_profit: 最小收益阈值

        Returns:
            按收益排序的套利路径列表
        """
        opportunities = []

        for item_name in self.items.keys():
            result = self.calc_arbitrage(item_name, start_chaos)
            if result and result.profit_chaos > min_profit:
                opportunities.append(result)

        # 按每金币获利排序(从高到低)
        opportunities.sort(key=lambda x: x.profit_per_gold, reverse=True)
        return opportunities

    def get_best_opportunity(self, start_chaos: float = 1.0) -> Optional[TradePath]:
        """获取最佳套利机会"""
        opportunities = self.find_all_opportunities(start_chaos)
        return opportunities[0] if opportunities else None


def print_result(result: TradePath):
    """打印套利结果"""
    print(f"\n{'='*60}")
    print(f"物品: {result.item_name}")
    print(f"起始: {result.start_chaos:.2f} 混沌")
    print(f"结束: {result.end_chaos:.2f} 混沌")
    print(f"收益: {result.profit_chaos:.2f} 混沌 ({result.profit_chaos/result.start_chaos*100:.2f}%)")
    print(f"手续费: {result.total_gold_fee} 金币")
    print(f"每金币获利: {result.profit_per_gold:.6f} 混沌")
    print(f"{'='*60}")
    print("交易步骤:")
    for step in result.steps:
        print(f"  {step['step']}. {step['action']}")
        print(f"     {step['result']} (汇率: {step['rate']})")
        print(f"     手续费: {step['gold_fee']} 金币")


def main():
    """主函数"""
    calc = ArbitrageCalculator()

    # 从JSON文件加载
    calc.load_from_json('price.json')

    print("加载的数据:")
    print(f"  神圣石: 1 神圣 = {calc.divine_info.chaos} 混沌")
    print(f"  物品数量: {len(calc.items)}")
    for name, item in calc.items.items():
        print(f"    {name}: 混沌价格={item.chaos}, 神圣价格={item.divs}, 手续费={item.golds}")

    # 查找所有套利机会
    print("\n" + "="*60)
    print("套利分析 (混沌 -> 物品 -> 神圣 -> 混沌)")
    print("="*60)

    opportunities = calc.find_all_opportunities(start_chaos=1)

    if not opportunities:
        print("\n未找到有收益的套利机会")
        # 显示所有结果(包括亏损的)
        for item_name in calc.items.keys():
            result = calc.calc_arbitrage(item_name, 1)
            if result:
                print_result(result)
    else:
        print(f"\n找到 {len(opportunities)} 个有收益的套利机会:\n")
        for i, result in enumerate(opportunities, 1):
            print(f"\n--- 机会 {i} ---")
            print_result(result)


if __name__ == "__main__":
    main()