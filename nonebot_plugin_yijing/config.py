from __future__ import annotations

from typing import Literal

from nonebot import get_plugin_config
from pydantic import BaseModel, Field, SecretStr


class YijingConfig(BaseModel):
    """插件配置。

    所有硬币/铜钱输入统一使用“正/反”，默认正=3、反=2。
    """

    yijing_default_method: Literal["coin", "yarrow"] = Field(
        default="coin", description="默认起卦方式：coin=三枚铜钱法，yarrow=大衍筮法模拟"
    )
    yijing_positive_face: str = Field(default="正", description="铜钱正面输入词")
    yijing_negative_face: str = Field(default="反", description="铜钱反面输入词")
    yijing_positive_value: int = Field(default=3, description="铜钱正面的数值")
    yijing_negative_value: int = Field(default=2, description="铜钱反面的数值")

    yijing_group_default_enabled: bool = Field(default=True, description="新群默认是否启用")
    yijing_cooldown_seconds: int = Field(default=60, ge=0, description="群级冷却秒数")
    yijing_daily_limit_per_user: int = Field(default=10, ge=1, description="单用户每日起卦次数")
    yijing_duplicate_window_minutes: int = Field(default=30, ge=1, description="短期相似问题窗口")
    yijing_history_minutes_for_llm: int = Field(default=120, ge=1, description="默认传给 LLM 的历史窗口")
    yijing_store_question: bool = Field(default=True, description="是否保存原始问题文本")
    yijing_user_hash_salt: str = Field(default="change-me", description="用户ID哈希盐")

    yijing_render_scale: float = Field(default=2.0, ge=1.0, le=4.0, description="HTML 渲染倍率")
    yijing_render_width: int = Field(default=900, ge=640, le=1600, description="长图宽度")

    yijing_llm_enabled: bool = Field(default=False, description="是否启用 OpenAI 兼容 LLM")
    yijing_llm_base_url: str = Field(default="", description="OpenAI 兼容接口 base_url")
    yijing_llm_api_key: SecretStr | None = Field(default=None, description="LLM API Key")
    yijing_llm_model: str = Field(default="", description="LLM 模型名")
    yijing_llm_timeout_seconds: int = Field(default=30, ge=3, le=120, description="LLM 请求超时")


plugin_config = get_plugin_config(YijingConfig)
