"""
自动扫描通货价格并生成 price.json 格式数据
"""

import pyautogui
import pyperclip
import time
import random
import numpy as np
from paddleocr import PaddleOCR
from typing import Optional, Dict, List
import os
import cv2
import json

pyautogui.PAUSE = 0.04
pyautogui.FAILSAFE = True

# 禁用模型下载检查
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['FLAGS_use_mkldnn'] = '0'


class FaustPriceScanner:
    """通货价格扫描器 - 自动生成 price.json 格式数据"""

    def __init__(self, use_gpu: bool = False):
        print("正在初始化 PaddleOCR...")
        self.ocr = PaddleOCR(
            use_angle_cls=True, lang="ch", use_gpu=use_gpu,
            det_db_thresh=0.5, rec_char_type='ch',
            det_db_score_mode="slow", use_mkldnn=True
        )

        # 屏幕区域坐标
        main_l, main_t, main_r, main_b = 509, 106, 1427, 966
        self.region = (main_l, main_t, main_r - main_l, main_b - main_t)
        self.price_open_region = (858, 264, 100, 130)
        self.price_compete_region = (860, 460, 100, 130)
        self.hover_pos = (947, 182)
        self.exit = (1399, 113)

        # 价格数据
        self.price_data: Dict = {}

        print("价格扫描器已就绪")

    def _ocr(self, region=None, debug=True, name=None) -> List:
        """OCR 识别指定区域"""
        region = region or self.region
        img = pyautogui.screenshot(region=region)
        img_np = np.array(img)
        result = self.ocr.ocr(img_np, cls=True)
        lines = result[0] if result and result[0] else []

        if debug:
            dbg = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            for line in lines:
                pts = np.array(line[0], np.int32)
                cv2.polylines(dbg, [pts], True, (0, 255, 0), 2)
                cv2.putText(dbg, line[1][0], tuple(pts[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            os.makedirs("debug", exist_ok=True)
            cv2.imwrite(f"debug/{name or int(time.time()*1000)}.jpg", dbg)

        return lines

    def click(self, keyword: str, dx=0, dy=0, clicks=1, fuzzy=False, debug=True) -> bool:
        """点击关键字位置"""
        for _ in range(12):
            lines = self._ocr(debug=debug)
            for line in lines:
                text = line[1][0]

                if keyword not in text:
                    continue

                box = np.array(line[0])
                center_x, center_y = box.mean(axis=0).astype(int)

                global_x = self.region[0] + center_x + dx
                global_y = self.region[1] + center_y + dy

                pyautogui.moveTo(global_x, global_y,
                                 duration=0.2 + random.random() * 0.2,
                                 tween=pyautogui.easeOutQuad)
                pyautogui.click(clicks=clicks)
                return True

            time.sleep(0.01)

        print(f"[×] 点击失败：未找到关键字 → {keyword}")
        return False

    def go_home(self):
        """返回主界面"""
        pyautogui.moveTo(self.exit)
        time.sleep(0.05 + random.random() * 0.08)
        pyautogui.click(button='left')

    def search_and_select(self, name: str) -> bool:
        """搜索并选择物品"""
        if not self.click("请在此输入关键词", debug=False):
            self.go_home()
            self.click("通货兑换", wait=1.8)
            if not self.click("请在此输入关键词", debug=False):
                return False

        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyperclip.copy(name)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.75)

        for _ in range(8):
            if self.click(name, fuzzy=True, debug=False):
                return True
            time.sleep(0.55)

        print(f"[×] 未找到物品: {name}")
        return False

    def set_buy(self, name: str):
        """设置买入物品"""
        self.click("我需要", dy=40, debug=False)
        self.search_and_select(name)

    def set_sell(self, name: str):
        """设置卖出物品"""
        self.click("我拥有", dy=40, debug=False)
        self.search_and_select(name)

    @staticmethod
    def _extract_number(text: str) -> Optional[tuple]:
        """提取价格数字，返回 (买价, 卖价) 或 None"""
        cleand = text.replace(' ', '').replace(',', '.').replace('，', '.').replace('。', '.') \
                     .replace('O', '0').replace('o', '0').replace('l', '1').replace('I', '1')
        if ':' in cleand:
            buy, sell = cleand.split(':')
            try:
                return float(buy), float(sell)
            except ValueError:
                return None
        return None

    def read_price(self, max_retry: int = 3) -> Dict:
        """读取当前交易对的价格"""
        result = {"chaos": None, "divs": None, "golds": 0}

        for attempt in range(max_retry):
            print(f"  第 {attempt + 1}/{max_retry} 次尝试...", end=" ")

            x, y = self.hover_pos
            pyautogui.moveTo(x, y, duration=0.15 + random.random() * 0.1)

            pyautogui.keyDown('alt')
            time.sleep(0.05)

            temp_sell = None
            temp_buy = None

            for _ in range(random.randint(6, 8)):
                # 上半区：开放卖单
                img1 = pyautogui.screenshot(region=self.price_open_region)
                res1 = self.ocr.ocr(np.array(img1), cls=True)
                if res1 and res1[0]:
                    for line in res1[0]:
                        parsed = self._extract_number(line[1][0])
                        if parsed:
                            temp_sell = parsed[1] / parsed[0] if parsed[0] else 0
                            break

                # 下半区：竞品买单
                img2 = pyautogui.screenshot(region=self.price_compete_region)
                res2 = self.ocr.ocr(np.array(img2), cls=True)
                if res2 and res2[0]:
                    for line in res2[0]:
                        parsed = self._extract_number(line[1][0])
                        if parsed:
                            temp_buy = parsed[1] / parsed[0] if parsed[0] else 0
                            break

                time.sleep(0.01 + random.random() * 0.05)

            pyautogui.keyUp('alt')
            time.sleep(0.05)

            if temp_sell or temp_buy:
                result["chaos"] = temp_sell if temp_sell else None
                result["divs"] = temp_buy if temp_buy else None
                print(f"成功: chaos={temp_sell}, divs={temp_buy}")
                break
            else:
                print("未读到价格")

            time.sleep(0.2)

        return result

    def scan_divine_price(self) -> float:
        """扫描神圣石的混沌价格"""
        print("\n[扫描神圣石价格]")
        self.go_home()

        if not self.click("通货兑换", debug=False):
            print("无法打开通货兑换界面")
            return 0

        self.set_sell("神圣石")
        self.set_buy("混沌石")

        info = self.read_price()
        divine_price = info.get("chaos", 0) or 0

        self.price_data["div"] = {
            "chaos": divine_price,
            "divs": 1,
            "golds": 500  # 神圣石固定手续费
        }

        print(f"神圣石价格: {divine_price} 混沌")
        return divine_price

    def scan_item(self, item_name: str, gold_fee: int = 100) -> Dict:
        """扫描单个物品的价格"""
        print(f"\n[扫描物品: {item_name}]")
        self.go_home()

        if not self.click("通货兑换", debug=False):
            print("无法打开通货兑换界面")
            return {}

        # 扫描混沌价格
        self.set_sell(item_name)
        self.set_buy("混沌石")
        chaos_info = self.read_price()
        chaos_price = chaos_info.get("chaos", 0) or 0

        # 扫描神圣价格
        self.set_sell(item_name)
        self.set_buy("神圣石")
        divine_info = self.read_price()
        divs_price = divine_info.get("divs", 0) or 0

        result = {
            "chaos": chaos_price,
            "divs": divs_price,
            "golds": gold_fee
        }

        print(f"  {item_name}: chaos={chaos_price}, divs={divs_price}, golds={gold_fee}")
        return result

    def scan_all(self, items: List[tuple]) -> Dict:
        """
        扫描所有物品价格

        Args:
            items: [(物品名, 手续费), ...] 列表

        Returns:
            完整的价格数据字典
        """
        print("=" * 50)
        print("开始扫描通货价格")
        print("=" * 50)

        # 先扫描神圣石
        divine_price = self.scan_divine_price()
        if divine_price <= 0:
            print("警告: 神圣石价格读取失败，使用默认值 360")
            self.price_data["div"] = {"chaos": 360, "divs": 1, "golds": 500}

        # 扫描其他物品
        for item_name, gold_fee in items:
            time.sleep(0.5)  # 每次扫描间隔
            item_data = self.scan_item(item_name, gold_fee)
            if item_data:
                self.price_data[item_name] = item_data

        print("\n" + "=" * 50)
        print("扫描完成")
        print("=" * 50)

        return self.price_data

    def save_to_json(self, filepath: str = "price.json"):
        """保存价格数据到 JSON 文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.price_data, f, ensure_ascii=False, indent=4)
        print(f"已保存到 {filepath}")


def main():
    # 要扫描的物品列表: (物品名, 手续费)
    ITEMS_TO_SCAN = [
        ("神圣石", 500),
        ("混沌石", 100),
        # 添加更多物品...
    ]

    # 过滤掉神圣石(已单独处理)
    items = [(name, fee) for name, fee in ITEMS_TO_SCAN if name != "神圣石"]

    scanner = FaustPriceScanner(use_gpu=False)
    scanner.scan_all(items)
    scanner.save_to_json()

    # 打印结果
    print("\n价格数据:")
    print(json.dumps(scanner.price_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()