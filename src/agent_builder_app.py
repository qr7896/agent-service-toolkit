"""Agent Builder 界面（阶段 22 第三块）。

独立入口，不动原有聊天页面：

    streamlit run src/agent_builder_app.py

逻辑全在 `agents/agent_builder.py`（不依赖 Streamlit），这里只做渲染与收集输入。
编辑的是 `config/agents/*.yaml`——也就是阶段 22 第一块定义的那份数据；改完重启服务
即生效，因为注册表在启动时读取配置。
"""

import streamlit as st

from agents.agent_builder import AGENTS_DIR, delete_config, list_configs, save_config
from agents.agent_config import AgentConfigError
from agents.agents import CONFIGURABLE_TOOLS

st.set_page_config(page_title="Agent Builder", layout="wide")
st.title("Agent Builder")

existing = list_configs()

with st.sidebar:
    st.caption(f"配置目录：{AGENTS_DIR}")
    names = [item["file"] for item in existing]
    selected = st.selectbox("已有配置", ["— 新建 —", *names]) if names else "— 新建 —"

current: dict = {}
if selected != "— 新建 —":
    current = next((item.get("config") or {} for item in existing if item["file"] == selected), {})
    if error := next((item.get("error") for item in existing if item["file"] == selected), None):
        st.error(error)

with st.form("agent_config"):
    key = st.text_input("key", value=str(current.get("key") or ""))
    description = st.text_input("description", value=str(current.get("description") or ""))
    system_prompt = st.text_area(
        "system_prompt", value=str(current.get("system_prompt") or ""), height=240
    )
    tools = st.multiselect(
        "tools",
        options=sorted(CONFIGURABLE_TOOLS),
        default=[t for t in (current.get("tools") or []) if t in CONFIGURABLE_TOOLS],
    )
    rounds = st.number_input(
        "max_tool_rounds", min_value=1, max_value=50, value=int(current.get("max_tool_rounds") or 6)
    )
    submitted = st.form_submit_button("保存")

if submitted:
    try:
        path = save_config(
            {
                "key": key,
                "description": description,
                "system_prompt": system_prompt,
                "tools": tools,
                "max_tool_rounds": int(rounds),
            },
            set(CONFIGURABLE_TOOLS),
        )
        st.success(f"已保存 {path.name}（重启服务后生效）")
    except AgentConfigError as exc:
        st.error(str(exc))

if selected != "— 新建 —":
    if st.button(f"删除 {selected}"):
        try:
            delete_config(str(current.get("key") or selected.removesuffix(".yaml")))
            st.success("已删除")
        except AgentConfigError as exc:
            st.error(str(exc))

st.dataframe(
    [
        {
            "file": item["file"],
            "key": (item.get("config") or {}).get("key", ""),
            "tools": len((item.get("config") or {}).get("tools") or []),
            "error": item.get("error", ""),
        }
        for item in existing
    ],
    use_container_width=True,
)
