# Codex Quant Agent + Skill Pack

这个压缩包包含：

- `AGENTS.md`：放在量化项目根目录，用于约束 Codex 的整体行为；
- `.agents/skills/quant_data_backtest/SKILL.md`：Codex Skill，用于数据获取、策略生成与回测；
- `.agents/skills/quant_data_backtest/references/data_compliance_checklist.md`：数据合规检查清单；
- `prompts/start_quant_project_prompt.md`：可直接复制给 Codex 的启动提示词。

## 使用方法

1. 解压到你的量化项目根目录，例如：

```text
D:\AI REASONER\quant_etf_project
```

2. 在该目录打开 PowerShell：

```powershell
cd "D:\AI REASONER\quant_etf_project"
codex
```

3. 把 `prompts/start_quant_project_prompt.md` 里的内容复制给 Codex。

如果 Codex 没有自动识别技能，可以在提示词中明确写：

```text
请读取 .agents/skills/quant_data_backtest/SKILL.md 并严格按其中规则执行。
```
