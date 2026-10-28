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

默认先将完整应用窗口／完整当前页面按原始比例 contain：scale=min((框宽−32)/原图宽,(框高−32)/原图高)。Logo、顶部、左侧导航和页面空白均保留，留白沿用统一背景。无需包含无关桌面，也不要求长网页一次展示全文。禁止以预裁切的模型列表、积分条、按钮、局部结果区直接起镜；旧素材只有局部图时找完整原件或补采。隐私由单独遮罩处理，不以去掉侧栏代替。

细节镜头在同一张原图／连续源片上推进：完整窗口建立整体 → 红框定位 → 随对应口播平滑放大／平移 → 重点停留。只有完整界面就足以说明口播时不加变焦。前后幕接续同一操作可连续保持已经建立的镜头，不能另换一张局部截图、跳变尺度或按每段字幕重复缩放。

逐幕 `source_camera={targetRect:[x,y,w,h],fromFrame:30,toFrame:78}` 指定原图坐标中的完整目标区域和幕内起止帧；30fps，起点须先留完整窗口，落点后留阅读时间。组装为 `sourceCamera`；没有此字段时始终完整展示。`crop/sourceRect` 不再驱动 v2 新制作的起镜；历史 v1 复现仍使用其独立旧工程。

缩放和平移使用同一个平滑进度，同时插值**缩放系数与平移量**，不要分别插值源图中心和缩放再相乘，以免角落的积分卡在中途滑出画框。宽高等比，外框、品牌和字幕固定；红框与隐私遮罩使用相同变换。逐帧核对目标区域始终处于固定内框，首／中／末均应可定位重点，不弹跳、不装饰性漂移。

矩形标注仍使用原图像素：`highlights=[{rect:[x,y,w,h],color:"#D93232",strokeWidth:5}]`，组装为 `sourceHighlights`；边框粗细以成片画布像素计。标注包住真实目标并留边，不压字或遮掉限定词。`redactions=[{rect:[x,y,w,h],color:"#EEF0F2"}]` 是独立隐私层，原片保持不变，完整窗口及运镜途中都须遮住对应私密区域。标注与遮罩均完整位于原始图像内。

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
