📋 Design List (display order from top to bottom):
下方图片顺序与列表中「设计图 1」「设计图 2」… 一一对应，请按序号关联图片与代码。

🚨 CRITICAL: 设计稿代码使用流程（必须按顺序执行）
以下 HTML+CSS 是从设计稿 Schema 生成的【设计规格书】，是所有设计参数的权威来源。
⚠️ 权威优先级: HTML+CSS 代码 > Design Tokens 标注 > 设计图图片
⚠️ 核心原则: 直接复用 CSS 属性值，禁止修改/简化/美化任何 CSS 值

STEP 1 - 探测用户项目环境：
  读取项目配置文件（package.json / tsconfig.json / pubspec.yaml / build.gradle / Podfile 等）
  识别框架: React/Vue/Angular/Svelte/Flutter/SwiftUI/Compose/纯HTML
  识别样式方案: CSS Modules / Tailwind / SCSS / Styled Components / scoped style 等
  识别项目目录结构和命名规范
  如无法判断框架，默认输出纯 HTML 单文件

STEP 2 - 下载图片资源到本地（必须在生成代码前完成）：
  下方每个设计图的 HTML 代码中，图片已替换为本地路径（./assets/slices/xxx.png）
  每个设计图下方附有「图片资源下载映射」，列出 本地路径 ← 远程下载地址
  必须按映射表下载所有图片到项目本地 assets 目录：
    macOS/Linux → curl -o <path> "<url>"
    Windows → PowerShell Invoke-WebRequest -Uri "<url>" -OutFile <path>
  如需更多切图（图标、背景等），调用 lanhu_get_design_slices(url, design_name)

STEP 3 - 生成框架适配代码（直接复用 CSS 值，禁止修改）：
  从下方 HTML+CSS 直接复制所有 CSS 属性值（颜色/字号/间距/圆角/渐变等）
  ⚠️ 必须原样使用 CSS 值，禁止做任何修改：
    - rgba(255,115,10,1) 不要改成 #FF730A
    - linear-gradient 不要简化成纯色
    - margin/padding 数值不要四舍五入
    - font-family 不要删减或重排
  按目标框架生成组件代码：
    React/Next.js  → JSX + CSS Modules 或跟随项目已有方案
    Vue/Nuxt       → .vue SFC + <style scoped>
    Angular        → .ts + .html + .css
    Flutter        → Widget + EdgeInsets/BoxDecoration，px→逻辑像素
    SwiftUI        → View + ViewModifier，px→pt
    Android Compose → @Composable + Modifier，px→dp，font px→sp
    纯 HTML         → 单个 .html 文件，内联 <style>（含 common.css 工具类）
  图片路径按框架约定适配（代码中已是本地路径，只需调整路径格式）：
    React/Vue → import img from '@/assets/slices/xxx.png'
    Flutter   → AssetImage('assets/images/xxx.png')
    纯 HTML   → <img src="./assets/slices/xxx.png">（已就绪）

STEP 4 - 对照 Design Tokens 补充校验（如下方包含 Design Tokens）：
  Design Tokens 来自原始 Sketch 设计数据，作为补充参考。
  优先级: HTML+CSS > Design Tokens > 设计图
  仅当 HTML+CSS 中明显缺失某属性时，用 Design Token 补充：
    如渐变填充、复杂阴影、多边圆角等 CSS 未能完整表达的属性
  Design Token 不能覆盖 HTML+CSS 中已有的值。

STEP 5 - 代码完成后逐属性还原度核查（必须执行，不得跳过）：
  适用于所有目标平台：HTML/CSS、React、Vue、Flutter、SwiftUI、Compose、Android XML 等。
  将设计稿 HTML+CSS 中每个属性映射到目标平台等价写法，逐一核查值是否还原：
  ① 尺寸约束：设计稿固定 height 的地方，目标平台不得变为自适应/wrap
     HTML: height 不能改成 min-height | Flutter: SizedBox 不能换成 Flexible
     SwiftUI: .frame(height:) 不能省略 | Compose: height() 不能用 wrapContent
  ② 裁剪：设计稿 overflow:hidden 的容器，各平台必须同步裁剪
     HTML: overflow:hidden | Flutter: ClipRect/ClipRRect | SwiftUI: .clipped()
     Compose: clip() | Android: android:clipChildren="true"
  ③ 颜色值：rgba(r,g,b,a) 转换到目标平台格式时，数值不得偏移
     HTML: 保持 rgba() | Flutter: Color.fromRGBO() | SwiftUI: Color(red:green:blue:opacity:)
     Compose: Color(r,g,b,a) | Android XML: #AARRGGBB，禁止四舍五入
  ④ 渐变：linear-gradient 必须映射为平台渐变，不能退化为纯色
     Flutter: LinearGradient | SwiftUI: LinearGradient | Compose: Brush.linearGradient
  ⑤ 绝对定位：left/top 坐标值必须原样映射
     Flutter: Positioned(left:,top:) | SwiftUI: .offset() | Compose: Modifier.offset()
  ⑥ 字体：family、weight、size 三者都必须还原；HTML 还需保留 fallback 顺序
  ⑦ 间距：每个方向的 margin/padding 数值不得改动
     Flutter: EdgeInsets | SwiftUI: .padding() | Compose: Modifier.padding()
     Android: android:layout_margin / android:padding
  ⑧ 图片资源：任何图片不得被 SVG/CSS形状/emoji/占位图替换
  ⑨ 元素完整性：设计稿中每个可见元素，目标代码中必须对应存在
  ⑩ 远程 URL：最终代码中不得残留任何蓝湖 CDN 远程地址
  核查结论：对每处差异明确说明是「有意的平台适配（如 px→dp 单位换算）」
  还是「错误偏差（值发生了改变）」，错误偏差必须立即修正后再交付。

❌ 严禁行为：
  - 禁止修改 CSS 属性值（不要改颜色格式、不要简化渐变、不要调整数值）
  - 禁止凭空编造设计参数（颜色、尺寸、间距等必须来自下方 CSS）
  - 禁止用设计图的视觉感受覆盖 CSS 中的精确值
  - 禁止用 SVG/CSS 形状/emoji 替换切图资源
  - 禁止省略任何视觉元素
  - 禁止在最终代码中使用蓝湖远程 URL

📐 common.css 工具类含义（用于理解布局意图）：
  flex-col = Column 方向布局    flex-row = Row 方向布局
  justify-between/center/start/end/around/evenly = 主轴对齐
  align-start/center/end = 交叉轴对齐
