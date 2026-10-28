# v2三技能接口与命令

口播Skill输出narration.json：schema_version=1.0、project_id、brand=ai-coach、status=draft/confirmed、title、35个按序scenes。每幕id、narration、intent、evidence_needed。正式组装只接受confirmed；诊断可用draft，不能称正式成片。

visual_plan.json由导演写，字段：schema_version、project_id、narration_path绝对路径、narration_sha256、scenes；默认22真实／13动态／0AI，调整两类比例时提供material_mix_rationale。真实至少20幕，其余为Remotion，不再接受ai_image。每幕按主视觉计一次；requests与assemble保存material_mix_report.json，ai计数保留为0便于历史报告比较。结构通过不代表动效质量合格。每幕包含id、原narration、audience_takeaway、visual_type、selection_reason、content_description、framing、timing。
- real_screenshot/real_recording：capture_request_id和capture_request（purpose、app、task_context、prompt可选、required_events、framing、readability_requirements）。同请求可给多幕，但目的不能冲突。source_start_seconds可选，仅决定源片起点。
- 真实幕标明media_surface="desktop"或"phone"，组装为mediaSurface；旧计划缺省desktop，不按长宽比推测。完整窗口起镜、固定框、等比与连续运镜规则见layout-and-overlay-guardrails.md。截图与录屏同设备用同一版式。
- motion_effect：effect={id:"本期自定义ID",params:{...本效果所需数据}}，可选renderer="custom"/"builtin"。ID不设创意白名单；在本期src/CustomEffects.tsx注册实际实现，见motion-effects.md。兼容旧库组件时仍使用title/items约束；重写旧库同名ID时标renderer="custom"以免套用旧参数约束。新主题在项目目录复制独立src及配置、复用node_modules，不改共享组件来承载某一期内容。锁文件保留参数，交付另保留该候选对应源码快照。
semantic_role可选，用于转场：question/summary/advice/cta从下推入，其余左右交替。episode、series_title、corner_logo_path、corner_logo、show_episode_marker可选。新项目将工作空间对应的brand_profile（miaodong_finance／caishu_ai_lab）写入visual_plan.json；显式配置优先，未设置时由scripts/brand_profiles.py按调用工作空间推断，assemble将最终模板配置保存到visual_plan.lock.json。narration.json中的brand=ai-coach沿用制作协议标识，不能用它推断成片Logo或CTA。

`requests`导出capture_request.json供real-ui-capture。返回capture_manifest.json：schema_version/project_id/assets；每项asset_id/request_id/scene_ids/type/path/app/task_title/captured_at/width/height，录屏有duration_seconds/events；semantic_support与qa（status/readability/stability/completeness/notes）必须真实填写，provenance.method可追溯。原始文件必须保留完整应用窗口／当前页面，不预裁改。旧清单crop仅保留历史信息，v2组装不再写为sourceRect；必须重新检查完整原件中的隐私和可读性。仅有局部原件时补采，不能靠取消crop假称完整。

真实资产可选`highlights=[{rect:[x,y,w,h],color:"#D93232",strokeWidth:5}]`：rect以完整原始图像像素计，必须位于原图内；strokeWidth以1080px成片画布计。组装为`sourceHighlights`，与原图使用相同缩放和平移。隐私层可用`redactions=[{rect:[x,y,w,h],color:"#EEF0F2"}]`，组装为`sourceRedactions`，全程随原图遮挡。

逐幕可选`source_camera={targetRect:[x,y,w,h],fromFrame:30,toFrame:78}`，组装为`sourceCamera`。坐标以完整原图计，帧为30fps幕内帧；起点大于0，落点早于本幕末尾。先留完整窗口，再依口播在同一原始素材上连续推进并停留；无此字段时全程完整窗口。以实际TTS时长校准帧数，不改口播以迁就镜头。需要跨幕连续镜头或多页展示时，在本期工程保持原图与变换连续，并保留对应源码快照；不自动从crop推断运镜。

新流程不生成image_brief、codex_image_manifest.json或image_assets.json，也不调用生图工具。历史文件保留，不用于新计划；assemble的--images参数仅保留旧调用签名兼容，不能绕过ai_image禁用校验。

复用音轨时audio_manifest.json：{"scenes":{"scene_01":{"text":"对应口播原文","path":"/实际音频.mp3","provider":"minimax"}}}。text必须精确匹配；未提供时诊断组装用系统语音并标为诊断，--formal走已配置MiniMax，失败不降级。

```bash
python3 scripts/director.py validate --plan /项目/visual_plan.json
python3 scripts/director.py requests --plan /项目/visual_plan.json --out /项目/requests
python3 scripts/director.py assemble --plan /项目/visual_plan.json --capture /项目/capture_manifest.json --out /项目/work/candidate-v2 --formal
# 在本技能remotion目录执行；输出候选，不能直接覆盖历史video.mp4
node node_modules/@remotion/cli/remotion-cli.js render src/index.ts AiCoachDailyDemo /项目/work/candidate-v2/video_candidate.mp4 --props=/项目/work/candidate-v2/remotion_props.json --codec=h264 --crf=17
```

完整视频必须带BGM。计划可写`bgm={path,volume,fadeInSeconds,fadeOutSeconds}`；未指定时由组装入口接入已有默认音乐（volume=0.15，淡入0.8秒、淡出1.6秒），`meta.bgm`含来源/hash/时长。BGM缺失、不可解码、音量无效不能静默跳过。用户明确要求无音乐时，用`bgm={enabled:false,omission_reason:"用户明确要求的原话或准确说明"}`并在输出记录例外。

scene_bindings.json记录最终素材/音频hash和duration_frames，visual_plan.lock.json及narration.lock.json保留对应版本。正式影像来源检查与验收见acceptance-v2。

## 大模型长型号：口播简称与完整型号字幕

适用范围仅是讲解大模型时，型号过长、一长串名称影响朗读的情况。不是所有名称、术语或编号的通用改写规则；短型号照常使用，同段不同版本仍须能区分。

`narration`始终是送入TTS的实际口播。处理大模型长型号时，在narration场景和visual_plan对应场景中保存相同的`caption_aliases`：

```json
{"narration":"付费模型，先试DeepSeek最新模型。","caption_aliases":[{"spoken":"DeepSeek最新模型","display":"DeepSeek最新模型（DeepSeek V4.1 Flash）"}]}
```

`spoken`必须真实出现在本幕口播中，不为空、不重复冲突；映射仅限本幕，不根据品牌名猜版本或推理设置。`scripts/caption_aliases.py`在口播分句完成后插入`display`，不改变TTS输入、不递归替换已经插入的型号。简称跨两段字幕时只合并必要边界；不含映射的旧稿保持原字幕。找不到对应词时明确报错，不能静默丢失型号。音频manifest的text仍必须精确匹配narration。已有字幕override也先保存口播文字，再展开映射，避免重复括号。

检查展开后的长字幕在手机画幅中的换行、遮挡和阅读时间；数字与单位不得拆成孤立的字幕。必要时按语义调整受影响的字幕边界，保留连续时序，不为了放下型号缩小整片字体或改动已认可动效。修订已认可成片时，只重新生成口播实际变化的音轨；完整型号只改变字幕的幕复用原音轨。按新自然语音时长组装，重新生成SRT并核对成片。

## 已确认的两段两图接入
每项Skill默认启动录像、结果录像、提示词截图、成果截图。采集交付沿用用户已确认的1127点窗口预设，不要求为接入重拍、裁切或压缩报告。同一request/type有多份资产时，每幕以capture_asset_id明确选择asset_id；source_start_seconds指定该源片内起点。已获用户实际观看认可的原片可以记录认可来源并accepted，不再因Agent未连续观看而降为pending。视频端负责选段与口播对应及最终构图检查；原始素材合格与成片可用分别记录。

## 公众号素材复用

从已确认公众号文章转化35幕口播，sources保留文章绝对路径或原文链接；本期visual_plan.json记录source_article_path，并明确brand_profile=caishu_ai_lab。口播允许为视频重排、压缩，转化稿确认后仍遵守逐幕不可擅改契约。

读取公众号的原始截图、录屏与采集清单，根据新分镜建立本期capture_manifest.json：project_id使用视频项目ID，request_id/scene_ids按新分镜绑定；path沿用真实原件，保留asset_id、app、captured_at、width/height、duration_seconds/events及真实hash。provenance记录source_project_id、source_manifest和source_asset_id，semantic_support说明它怎样支撑当前口播。重新检查本期可读性、隐私、时效和录屏起点／时长后才记录qa.status=accepted，不修改原公众号清单，不伪造采集或审核。

```bash
python3 scripts/director.py requests --plan /视频项目/visual_plan.json --reuse-manifest /视频项目/capture_manifest.json --out /视频项目/requests
```

此命令验证绑定、accepted状态、文件和hash，已可用素材跳过采集；capture_request.json只包含缺口，reused_capture_manifest.json保留已绑定原件。未核验素材不能作为复用输入。补采完成后将复用项和新采集项合并到本期capture_manifest.json，保留来源与各自QA，再照常assemble。需要多少张、复用哪一段由导演逐幕决定，不按文章图片顺序直接拼片。

## 财叔现役动效接入

财叔默认`motion_style=caishu-editorial-v1`，组装写入`meta.motionStyle`；秒懂仍为`white-line-v1`。本期有明确的其他样式选择时写`motion_style`保留选择。此字段记录制作选择，不自动把场景改成合格设计。

财叔先创建本期独立Remotion工程，再运行`python3 scripts/seed_motion_style.py --remotion-dir /项目/视频/03_制作/remotion --brand-profile caishu_ai_lab`，按`references/motion-style-caishu-editorial.md`创作、注册场景并验收。不要为接入样式覆盖本期已有源码。正式素材/配音/品牌与BGM协议保持不变。
