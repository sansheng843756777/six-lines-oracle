# 六爻神数 v8.29 🏆

[![GitHub](https://img.shields.io/badge/GitHub-six--lines--oracle-blue?style=flat-square&logo=github)](https://github.com/sansheng843756777/six-lines-oracle)

融合传统六爻卦象与现代足球数据的混合预测模型。

## 架构

```
generate_v8()
├── generate_v7()           六维因子 + 七大新因子 + 五行卦象
├── v8.6 精简因子           AFC/CAF铁桶/星线/门将/纪律
├── v8.29 超长补时          stam/dep/cb/rot_stop
├── v8.27 惨败锁壳
├── v8.21 bucket_draw       铁桶平局
├── v8.10 slow_start        欧洲慢热
├── 赔率交叉验证
└── 三遍自查 (run_triple_check)
```

## 使用

```bash
# 全量预测
python six_lines_oracle_v8.py

# 单场预测
python six_lines_oracle_v8.py Argentina "Cape Verde"

# 通过脚本
bash scripts/oracle_predict.sh Spain Austria
```

## 回测准确率

9场淘汰赛方向准确率 **78%** (7/9)

| 场次 | 实际 | 预测 | 方向 |
|:----|:----:|:----:|:----:|
| 巴西 vs 日本 | 2-1 | 2-1 | ✅ |
| 德国 vs 巴拉圭 | 1-1→点球 | 2-1 | ❌ |
| 荷兰 vs 摩洛哥 | 1-1→点球 | 1-1→点球 | ✅ |
| 科特迪瓦 vs 挪威 | 1-2 | 1-1→点球 | ❌ |
| 法国 vs 瑞典 | 3-0 | 3-0 | ✅ |
| 墨西哥 vs 厄瓜多尔 | 2-0 | 2-0 | ✅ |
| 英格兰 vs 刚果金 | 2-1 | 3-1 | ✅ |
| 比利时 vs 塞内加尔 | 2-2→点球 | 2-1→点球 | ✅ |
| 美国 vs 波黑 | 2-0 | 2-0 | ✅ |

---

## ☕ 打赏支持  🙏

如果这个项目对您有帮助，请打赏一杯咖啡支持持续开发！

**微信扫码打赏**

![微信收款码](assets/wechat_qr.jpg)

或通过 GitHub Sponsor 赞助：https://github.com/sponsors/sansheng843756777

---

## 📜 License

MIT
