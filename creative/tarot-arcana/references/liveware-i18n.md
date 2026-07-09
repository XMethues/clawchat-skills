# Liveware 前端国际化 (i18n) 架构

Tarot Arcana 的静态 HTML 前端 (`liveware/static/index.html`) 支持 URL query 参数指定语言，默认英语。

## 架构概览

支持 URL query 参数指定语言，默认英语，不依赖任何外部库：

```
window.location.search?lang=zh
    ↓
const LANG = 'zh' | 'en'   ← 语言检测层（query → 默认值）
    ↓
const i18n = { zh: {...}, en: {...} }   ← 翻译定义层
    ↓
t('key') / applyStaticI18n()   ← 应用层
```

## 语言检测

支持三种方式，优先级从上到下：

```javascript
const LANG = (() => {
  const params = new URLSearchParams(window.location.search);
  const queryLang = params.get('lang');
  if (queryLang === 'zh') return 'zh';
  if (queryLang === 'en') return 'en';
  // 自动检测浏览器语言
  const navLang = (navigator.language || navigator.userLanguage || '').toLowerCase();
  if (navLang.startsWith('zh')) return 'zh';
  return 'en';
})();
```

| 方式 | 示例 | 说明 |
|------|------|------|
| URL query 参数 | `/?lang=zh` | 最高优先级，显式指定语言 |
| 浏览器语言 | `navigator.language` | 自动检测，`zh` 开头 → 中文，其他 → 英语 |
| 默认值 | 无匹配 | 英语 |

**设计考量：** query 参数优先使外部调用（如机器人、iframe、分渠道分发）能精确控制语言，不受用户浏览器设置影响。无匹配时自动检测 `navigator.language`，浏览器为中文（`zh` 前缀）时自动显示中文，否则显示英语。`?lang=en` 可强制覆盖浏览器检测。

## 预填问题 (`?question=`)

支持通过 URL query 参数 `question` 预填问题输入框，方便从外部链接直接跳转到指定问题的解读：

```
/?lang=zh&question=我该如何看待这段关系
```

初始化代码末尾自动检测并填入：

```javascript
const urlParams = new URLSearchParams(window.location.search);
const presetQuestion = urlParams.get('question');
if (presetQuestion) {
  questionInput.value = presetQuestion;
  updateQuestionMeta();
}
```

与 `lang` 参数完全正交 — 可以独立使用，也可以组合使用。

## 翻译定义 (`i18n` 对象)

每个 key 对应一个翻译值。支持两种形式：

### 静态字符串

```javascript
zh: {
  btn_draw: '抽牌',
  btn_reset: '重置',
  oracle_heading: '🔮 塔罗解读',
},
en: {
  btn_draw: 'Draw Cards',
  btn_reset: 'Reset',
  oracle_heading: '🔮 Tarot Reading',
},
```

### 动态函数 (带参数)

```javascript
zh: {
  ritual_pick: (n) => `牌列已展开 · 双击选择 ${n} 张`,
  deck_remaining: (n) => `剩余 ${n} 张`,
},
en: {
  ritual_pick: (n) => `Spread ready · Double-click ${n}`,
  deck_remaining: (n) => `${n} remaining`,
},
```

## 静态 HTML 翻译 (`data-i18n` 属性)

静态 HTML 元素通过 `data-i18n` 属性标记，`applyStaticI18n()` 一次性替换：

```html
<h1 data-i18n="intro_heading_line1">塔罗占卜</h1>
<p data-i18n="step1">第 1 步：想好你的问题</p>
<button data-i18n="btn_draw">抽牌</button>
```

aria-label 使用 `data-i18n-aria`：

```html
<button data-i18n="btn_draw" data-i18n-aria="btn_draw_aria">抽牌</button>
```

**`applyStaticI18n()` 工作流程：**

1. 设置 `document.title` 和 `<html lang="...">`
2. 遍历所有 `[data-i18n]` 元素，替换 `textContent`
3. 遍历所有 `[data-i18n-aria]` 元素，设置 `aria-label`
4. 特殊处理 placeholder 属性（input/textarea）

## 动态 JS 字符串翻译

运行时生成的 DOM 元素通过 `t('key')` 调用翻译：

```javascript
// 创建按钮
const btn = document.createElement('button');
btn.textContent = t('btn_draw');
btn.setAttribute('aria-label', t('btn_draw_aria'));

// 带参数的动态字符串
statusEl.textContent = t('ritual_pick')(n);
```

## 添加新翻译

1. 在 `i18n.zh` 和 `i18n.en` 中添加对应的 key
2. 静态 HTML 元素：添加 `data-i18n="key"` 属性
3. 动态 JS 字符串：使用 `t('key')` 调用
4. 如果参数是动态的，使用函数形式

## 注意事项

- 原始中文字符串是默认值（i18n 定义中的中文），英文为备选
- 所有 `t('key')` 调用需确保 key 在 `i18n.zh` 和 `i18n.en` 中都存在
- 动态生成的元素（如卡牌、解读文本）通过 JS 的 `t()` 调用，不需要 `data-i18n` 属性