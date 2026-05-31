import streamlit as st
import pandas as pd
import json_repair
from openai import OpenAI

# ==========================================
# 1. 页面基本配置
# ==========================================
st.set_page_config(page_title="AI 分镜头拆解工具", layout="wide")
st.title("🎬 AI 智能分镜头脚本拆解工具 (智谱 GLM-4 强力驱动)")
st.markdown("输入文案或创意描述，一键生成标准分镜头脚本，并附带画面生成提示词。")

# ==========================================
# 2. 侧边栏配置区域
# ==========================================
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("输入你的智谱 API 密钥", type="password")
    st.info("💡 提示：已开启最高严谨模式与标点符号防崩溃指令，确保表格完美生成！")

# ==========================================
# 3. 主界面输入区域
# ==========================================
source_text = st.text_area(
    "📝 请输入原始文案、剧情描述或广告脚本：",
    height=200,
    placeholder="在此输入你的文字，例如驿卒送热食的荒诞武侠文案..."
)

generate_btn = st.button("🚀 开始智能化拆解分镜头", type="primary")

# ==========================================
# 4. 触发生成与展示逻辑
# ==========================================
if generate_btn:
    if not api_key:
        st.warning("⚠️ 导演，请先在左侧输入你的智谱 API 密钥哦！")
    elif not source_text:
        st.warning("⚠️ 请先输入一些文案描述内容哦！")
    else:
        with st.spinner("🧠 智谱 AI 导演正在疯狂构思分镜头，并精确控制 60 秒时长..."):
            try:
                # 初始化智谱客户端
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://open.bigmodel.cn/api/paas/v4/"
                )

                # 【终极防崩溃指令与自定义格式】
                system_prompt = """
                你是一个拥有20年经验的资深广告导演和分镜师。请将用户输入的文案拆解为专业的分镜头脚本。

                【极其重要的格式死命令】：
                1. 你必须且只能输出合法的纯 JSON 数组格式，不要包含任何 Markdown 代码块（如 ```json ）。
                2. 绝对禁止在 JSON 的 Value（字符串内容）内部使用英文双引号（"）！如果你需要在文本中引用内容或表达对话，必须且只能使用中文双引号（“”）或英文单引号（'）。

                【时长控制要求】：
                请合理分配每个镜头的预估时长，必须确保所有镜头的 `duration`（时长）总和严格等于 60 秒。

                【JSON 字段严格要求】：
                JSON 数组中的每个对象必须严格包含以下 8 个字段（请务必使用下面指定的英文 Key）：
                - "shot": 镜头号 (数字类型，如 1)
                - "visual": 画面描述 (详细描述画面中发生的事情)
                - "shot_type": 景别 (如：全景、中景、近景、特写等)
                - "camera_movement": 运镜 (如：固定定焦、缓慢推镜头、横向移镜等)
                - "narration": 旁白 (对应的台词或配音，如果没有请留空)
                - "props": 服装/道具 (画面中需重点呈现的人物穿着、关键物品或特殊设定)
                - "duration": 预估时长 (例如 '3s'，加总必须为 60s)
                - "mj_prompt": 英文生图提示词 (直接用于 AI 绘画的纯英文 Prompt，需包含主体、场景、上文提到的服装道具、灯光及摄影机视角，用逗号分隔)
                """

                # 请求智谱 API
                response = client.chat.completions.create(
                    model="glm-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"需要拆解的文案内容如下：\n{source_text}"}
                    ],
                    temperature=0.1,  # 极低温度，保证模型输出格式稳定，不自由发挥
                    max_tokens=4000
                )

                # 提取原始文本
                result_text = response.choices[0].message.content.strip()

                # 暴力提取法：只截取 [ ] 之间的部分，防止大模型说废话
                start_idx = result_text.find('[')
                end_idx = result_text.rfind(']')
                
                if start_idx != -1 and end_idx != -1:
                    clean_json_str = result_text[start_idx:end_idx+1]
                else:
                    clean_json_str = result_text

                # 【核心装甲】：使用 json_repair 强力解析
                storyboard_data = json_repair.loads(clean_json_str)

                # 转换为 Pandas DataFrame
                df = pd.DataFrame(storyboard_data)
                
                # 为了让网页展示更完美，将英文 Key 映射为中文表头
                df = df.rename(columns={
                    "shot": "镜头号",
                    "visual": "画面描述",
                    "shot_type": "景别",
                    "camera_movement": "运镜",
                    "narration": "旁白",
                    "props": "服装/道具",
                    "duration": "预估时长",
                    "mj_prompt": "英文生图提示词"
                })

                st.success("✅ 恭喜你！包含服装道具并控制在 60 秒的完美分镜表格已生成！")
                st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error("❌ 解析发生意外错误，请重试。")
                st.write("系统错误详情：", e)
                with st.expander("查看 AI 原始输出（供排查）"):
                    st.text(result_text)