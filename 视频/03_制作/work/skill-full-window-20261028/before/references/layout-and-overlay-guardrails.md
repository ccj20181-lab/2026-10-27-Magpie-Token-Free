# v2固定布局与组件边界

v2使用remotion/src/DirectorComposition.tsx。顶部黄色栏目胶囊radius45，红色期数radius60，Logo原样。媒体框radius0。不同组件各有职责，不能全局替换borderRadius。

两品牌共用此布局。调用秒懂金融工作空间默认miaodong_finance：秒懂金融Logo、“每天一个AI理财小技巧”；调用财叔工作空间默认caishu_ai_lab：财叔正式Logo、“每天一条AI干货”。财叔Logo沿用已有236×88及白底容器配置，秒懂金融沿用136×136。具体值由scripts/brand_profiles.py维护，组装后使用meta中的Logo配置，不能把财叔横向Logo硬塞成秒懂金融方形。show_episode_marker及本期已确认的横幅、Logo配置优先；财叔旧栏目文案按现役“每天一条AI干货”归一化，其他画面与制作标准保持原样。

## 真实素材统一展示规范

新制作不使用AI生图。真实截图和录屏共用对应设备版式，不因静图或视频改变位置。画布1080×1920，外背景#032442，媒体框直角、背景#F4F7FA，框内留白16px，内容居中。实现真源为 `remotion/src/realMediaLayout.ts`。

| 来源设备 | media_surface | left / top | 宽 × 高 |
|---|---|---|---|
| 电脑应用、网页、文档 | desktop | 28 / 510 | 1024 × 1080 |
| 手机真实截图、手机录屏 | phone | 270 / 510 | 540 × 1080 |

两个外框中心均为(540,1050)，顶部与底部对齐。visual_plan逐幕标明来源设备；旧计划缺省desktop以兼容电脑项目，不能根据图片宽高比猜设备。电脑的竖向菜单裁切仍为desktop。

素材按原始比例contain；有crop时先选源片完整语义区域，再等比容纳：scale=min((框宽−32)/区域宽,(框高−32)/区域高)，宽高采用同一scale。不得压扁、拉长、填满拉伸或用cover隐去上下文。空余区域保持统一背景，不把素材底色改成背景。

真实界面的默认取景是完整页面或完整结果区：保留任务标题/对象、结果内容和关键数值的相邻上下文。讲“消耗多少积分”时，应能同时看见交付物或完成结果、模型名称和用量；不把积分单行、单一数字或按钮窄条放大作为整幕主视觉。可以去除无关侧栏、空白及无关边缘，不要求机械展示整个桌面；能看懂发生了什么，同时看清重点。

需要突出某点时，先确定上述完整语义区，在清单记录crop=[x,y,w,h]，再用独立红框、箭头或下划线指向真实内容。原片不修改，不重写数值、不遮盖限定词。矩形标注可在资产写highlights=[{rect:[x,y,w,h],color:"#D93232",strokeWidth:5}]，rect使用原始图像像素，strokeWidth使用成片画布像素；组装为sourceHighlights，渲染按相同缩放及裁切偏移定位。框应包住目标并留边，不能压字、指错对象或越出展示范围。默认静态标注，不引入抖动、弹跳或装饰变焦。非矩形标注按本期实际需要实现，不自动补文案。

相邻同一操作沿用取景尺度。确需更近的细节镜头，先保留或同时展示能认清对象的整体画面；不能让观众只看到失去上下文的局部。固定外框不变，原图等比容纳，不以缩小所有文字换取无用途的全屏。

录屏在各幕Sequence内播放，以幕内帧加mediaStartFrame取源片；不能使用全片帧直接驱动源视频。外框、品牌与字幕始终固定。动效内容不受真实素材框约束，但须遵守品牌安全区与手机可读性。

字幕保持固定下方区域，不能被裁切。动态内容效果见motion-effects.md。手机尺寸查看与动态边界验证见acceptance-v2.md。

## 历史v1布局参考（仅复现旧工程时读取，不覆盖上面的v2）
# Layout and Overlay Guardrails

Read this file completely before rendering any preview or final AI Coach video.

## Fixed Canvas

- Canvas: 1080×1920, 9:16.
- Outer background: AI Coach deep blue template.
- Series header: `top 236`, `left 64`, `right 84`, `height 136`.
- Keep the episode marker aligned with the series label and the brand logo inside the same header row.

Do not move these layers for individual scenes.

## Standard Illustration Scene

Use the same stage for every 1376×768 horizontal illustration:

```text
top: 620
left: 52
right: 52
bottom: 610
object-fit: contain
overflow: hidden
```

Use the standard illustration caption:

```text
left: 76
right: 76
bottom: 300
```

Do not add scene-ID-specific position exceptions. A portrait phone screenshot is not a standard illustration; register it as recording/video content and use the recording stage.

## Standard Recording Scene

Use the same large stage for vertical phone recordings and truthful phone-screen video:

```text
top: 390
left: 28
right: 28
bottom: 290
object-fit: contain
```

Use the lower recording caption:

```text
left: 76
right: 76
bottom: 130
```

Preserve the original UI color, aspect ratio, app/chat title, and readable interaction area.

## Allowed Layers on Standard Content Scenes

Only these layers may appear:

1. fixed blue background;
2. fixed series title;
3. fixed episode marker;
4. fixed corner logo;
5. one approved illustration or recording;
6. one standard narration caption.

The illustration itself may contain short labels approved during image review. The renderer must not repeat or supplement them.

## Forbidden Automatic Overlays

Do not automatically render any of the following on illustration or recording scenes:

- scene `headline`;
- `step_label`;
- `annotation_note`;
- generated process labels;
- explanatory corner text;
- “AI在后台……” slogans;
- duplicated titles, scene numbers, arrows, badges, or callouts;
- text inferred from narration but not explicitly approved by the user.

Image-sequence notes may render only when the user explicitly approves the exact `sequence_notes` text. Never fall back from internal metadata such as `annotation_note`.

Title and CTA scenes are deliberate exceptions and must use their dedicated templates. Do not silently convert a normal content scene into a title or CTA scene to add more text.

## No Position Hacks

Do not special-case positions by scene number, topic, image filename, or current project. If an asset does not fit its assigned stage:

1. verify that its type is correct;
2. normalize a horizontal illustration to 1376×768;
3. register a portrait screen as recording/video content;
4. regenerate or recut the asset if necessary.

Do not solve an incorrect asset type with arbitrary top/bottom offsets.

## Layout QA Gate

Before the full render:

1. Render one representative illustration still.
2. Render one representative recording still.
3. Render one long-caption still from each type.
4. Confirm the header, episode marker, logo, asset, and caption do not overlap.
5. Confirm the illustration is visually centered and the recording is large enough to read.
6. Confirm no unapproved text exists outside the asset and standard caption.

After the full render, inspect scene boundaries as required by the recording guardrails. Do not deliver when any asset position, overlap, duplicated label, or unexplained annotation is visible.

## 2026-09-22 固定修订

全部新增矩形底板、图片与视频容器、字幕底板使用直角（borderRadius: 0），禁止圆角裁切素材。真实应用界面中的原生圆角保持原样。画面按内容实际比例完整展示，避免空白外框、无信息局部裁切；结果优先完整呈现一个有结论与依据的区块。Skill 输出不设置句数、字数硬上限，用短句和有依据的表格图示提高密度。

栏目标签例外：左上角“每天一个AI理财小技巧”保留原有黄色胶囊形圆角，不适用配图直角规则。不要把素材容器的修改扩大到品牌栏目标签。

左上角栏目标题与红色期数标识作为一组保留原版圆角样式：黄色栏目标签和红色#期数均不适用配图直角规则。
