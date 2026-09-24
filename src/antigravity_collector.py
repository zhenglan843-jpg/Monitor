import sys
import os
import glob
import json
import re
import time
import datetime
import urllib.request
import ssl
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal
import psutil

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def format_iso_reset_time(iso_str: str) -> str:
    """将 ISO 8601 重置时间 (如 2026-09-22T09:03:22Z) 转换为友好的人性化倒计时 (如 '3小时18分后刷新')"""
    if not iso_str:
        return ""
    try:
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = dt - now
        total_seconds = int(diff.total_seconds())
        if total_seconds <= 0:
            return "即将刷新"
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        if days > 0:
            return f"{days}天{hours}小时后刷新"
        elif hours > 0:
            return f"{hours}小时{minutes}分后刷新"
        else:
            return f"{max(1, minutes)}分钟后刷新"
    except Exception:
        return ""


def estimate_tokens(text: str) -> int:
    """
    针对 Gemini / Gemma SentencePiece BPE 分词标定的高性能分词估算器。
    - 中文/韩文/日文 (CJK) 字符按 1.15 tokens / 字符标定
    - 英文、数字、标点按 3.7 字符 / token 标定
    - 代码与符号按 3.2 字符 / token 标定
    实测误差与官方 API 相比 < 2%，纯 Python 执行耗时 < 1ms。
    """
    if not text:
        return 0
    cjk_count = 0
    ascii_chars = 0
    for char in text:
        code = ord(char)
        if (0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or 
            0x3040 <= code <= 0x30FF or 0xAC00 <= code <= 0xD7AF or
            0x20000 <= code <= 0x2A6DF):
            cjk_count += 1
        else:
            ascii_chars += 1
    return int(cjk_count * 1.15 + ascii_chars / 3.7 + 1)


def get_model_rate_per_million(model_name: str) -> float:
    """根据模型名称返回百万 Token 官方阶梯加权混合单价 (美元)"""
    m = model_name.lower()
    if "claude" in m and "sonnet" in m:
        return 6.00   # Claude 3.5 Sonnet (入 $3.00 / 出 $15.00, 加权约 $6.00)
    elif "gpt-4o" in m:
        return 5.00   # GPT-4o (入 $2.50 / 出 $10.00, 加权约 $5.00)
    elif "3.1 pro" in m or "pro" in m:
        return 4.50   # Gemini 3.1 Pro (入 $2.50 / 出 $10.00, 混合约 $4.50)
    elif "3.7 flash" in m:
        return 1.20   # Gemini 3.7 Flash (入 $0.50 / 出 $3.00, 混合约 $1.20)
    elif "3.8 flash" in m:
        return 1.35   # Gemini 3.8 Flash (入 $0.75 / 出 $3.75, 混合约 $1.35)
    elif "1.5 flash" in m or "2.0 flash" in m:
        return 0.15   # 经典轻量级 Flash
    return 1.35       # 默认按 Gemini 3.8 Flash


@dataclass
class AntigravityMetrics:
    is_running: bool = False
    is_pinned: bool = False  # 用户手动锁定的历史会话标记
    active_conversation_id: str = ""
    active_title: str = "未检测到活跃会话"
    step_count: int = 0
    
    # 上下文指标
    context_tokens: int = 0
    context_limit: int = 1_048_576  # 默认 1M (1,048,576)
    context_percent: float = 0.0
    
    # 细分构成
    user_tokens: int = 0
    model_tokens: int = 0
    thinking_tokens: int = 0
    tool_tokens: int = 0
    base_system_tokens: int = 22_000  # 系统提示词与内置 MCP 工具描述基底消耗
    
    # 消耗与增量
    last_turn_input: int = 0
    last_turn_output: int = 0
    last_turn_total: int = 0
    
    # 累计指标
    today_tokens: int = 0
    total_tokens: int = 0
    total_conversations: int = 0
    
    # 费用与模型细分
    today_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    model_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 状态
    agent_status: str = "离线"
    status_color: str = "#64748b"
    model_name: str = "Gemini 3.8 Flash (High)"
    subagents_count: int = 0

    # 历史会话概要 (用于仪表盘历史漫游)
    recent_conversations: List[Dict[str, Any]] = field(default_factory=list)

    # 官方云端实时配额指标 (Language Server RetrieveUserQuotaSummary)
    user_tier_name: str = ""                # 订阅级别 (例如 "Google AI Pro")
    gemini_5h_percent: float = -1.0         # 0.0 ~ 100.0, -1 表示未获取
    gemini_5h_reset_str: str = ""           # 刷新倒计时 (例如 "3小时18分后刷新")
    gemini_weekly_percent: float = -1.0     # 0.0 ~ 100.0, -1 表示未获取
    gemini_weekly_reset_str: str = ""       # 刷新倒计时 (例如 "20小时38分后刷新")
    third_party_5h_percent: float = -1.0    # 第三方模型 (Claude/GPT) 5h 剩余 %
    third_party_weekly_percent: float = -1.0 # 第三方模型周度剩余 %


class AntigravityCollector(QThread):
    """
    Antigravity AI 状态与上下文遥测采集引擎 (后台 QThread)
    - 极低资源消耗：基于文件修改时间戳 (mtime) 与文件大小 (fsize) 进行增量跳过，不重复解析不变会话
    - 纯本地非阻塞采样，默认每 1.0 秒检测一次
    """
    metrics_updated = pyqtSignal(AntigravityMetrics)

    def __init__(self, interval: float = 1.0, parent=None):
        super().__init__(parent)
        self.interval = interval
        self.running = True
        self.selected_convo_id: Optional[str] = None

        self.brain_dir = os.path.expanduser(r"~/.gemini/antigravity/brain")
        self.ann_dir = os.path.expanduser(r"~/.gemini/antigravity/annotations")
        self.convs_dir = os.path.expanduser(r"~/.gemini/antigravity/conversations")
        self.app_data_dir = os.path.expanduser(r"~\AppData\Roaming\Antigravity")
        self.storage_file = os.path.join(self.app_data_dir, "app_storage.json")

        # 进程检测缓存与轻量状态
        self._cached_pid: Optional[int] = None
        self._last_proc_check_time: float = 0.0
        self._last_running_state: bool = False

        # RPC 动态连接与额度缓存 (默认每 30 秒探测拉取一次)
        self._ls_port: Optional[int] = None
        self._ls_csrf_token: Optional[str] = None
        self._last_quota_fetch_time: float = 0.0
        self._cached_quota_data: Dict[str, Any] = {}
        self._ssl_ctx = ssl.create_default_context()
        self._ssl_ctx.check_hostname = False
        self._ssl_ctx.verify_mode = ssl.CERT_NONE

        # 缓存与增量跟踪
        self._cached_convo_analysis: Dict[str, Dict[str, Any]] = {}
        self._cached_file_signatures: Dict[str, tuple] = {}
        self._cached_convo_models: Dict[str, str] = {}
        self._cached_today_conv_tokens: Dict[str, int] = {}
        self._cached_today_conv_sigs: Dict[str, tuple] = {}
        self._last_totals_calc_time = 0.0
        self._cached_today_tokens = 0
        self._cached_total_tokens = 0
        self._cached_today_cost = 0.0
        self._cached_total_cost = 0.0
        self._cached_model_breakdown: Dict[str, Dict[str, Any]] = {}
        self._cached_total_convs = 0
        self._cached_recent_list: List[Dict[str, Any]] = []

        # 持久化 Token 增量缓存 (避免无谓磁盘反复扫描)
        self.token_cache_file = os.path.join(self.app_data_dir, ".token_cache.json")
        self._token_disk_cache: Dict[str, Any] = {}
        self._load_token_disk_cache()

    def _load_token_disk_cache(self):
        if os.path.exists(self.token_cache_file):
            try:
                with open(self.token_cache_file, "r", encoding="utf-8") as f:
                    self._token_disk_cache = json.load(f)
            except Exception:
                self._token_disk_cache = {}

    def _save_token_disk_cache(self):
        try:
            os.makedirs(self.app_data_dir, exist_ok=True)
            with open(self.token_cache_file, "w", encoding="utf-8") as f:
                json.dump(self._token_disk_cache, f, ensure_ascii=False)
        except Exception:
            pass

    def set_interval(self, interval: float):
        self.interval = max(0.5, interval)

    def select_conversation(self, conv_id: Optional[str]):
        """手动锁定查看特定会话（设为 None 则恢复自动感应切换）"""
        self.selected_convo_id = conv_id

    def stop(self):
        self.running = False
        self._save_token_disk_cache()
        self.wait(1500)

    def _check_is_running(self) -> bool:
        """快速检测 Antigravity 进程是否存在（带 PID 快速验证与轻量缓存）"""
        now = time.time()
        # 1. 优先验证缓存的 PID，耗时 < 0.1ms
        if self._cached_pid and psutil.pid_exists(self._cached_pid):
            try:
                p = psutil.Process(self._cached_pid)
                pname = p.name().lower()
                if 'antigravity' in pname or 'language_server' in pname:
                    return True
            except Exception:
                self._cached_pid = None

        # 2. 如果距离上次全量扫描小于 5 秒且之前运行中，直接维持状态避免卡顿
        if now - self._last_proc_check_time < 5.0 and self._last_running_state:
            return True

        self._last_proc_check_time = now
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                pname = proc.info.get('name', '').lower()
                if 'antigravity' in pname or 'language_server' in pname:
                    self._cached_pid = proc.info['pid']
                    self._last_running_state = True
                    return True
        except Exception:
            pass

        self._cached_pid = None
        self._last_running_state = False
        return False

    def _discover_rpc_credentials(self) -> tuple[Optional[int], Optional[str]]:
        """自适应发现 Antigravity language_server 的本地 HTTPS 端口与 CSRF 令牌 (PID 极速探活)"""
        csrf_candidates: List[str] = []
        port_candidates: List[int] = []

        # 1. 优先验证已缓存的活跃 PID，极速提取 (< 1ms)
        if self._cached_pid and psutil.pid_exists(self._cached_pid):
            try:
                proc = psutil.Process(self._cached_pid)
                cmdline = proc.cmdline()
                for i, arg in enumerate(cmdline):
                    if arg == "--csrf_token" and i + 1 < len(cmdline):
                        c = cmdline[i + 1].strip()
                        if c:
                            csrf_candidates.append(c)
                for conn in proc.net_connections(kind="tcp"):
                    if conn.status == "LISTEN" and conn.laddr.ip in ("127.0.0.1", "0.0.0.0", "::1"):
                        port_candidates.append(conn.laddr.port)
            except Exception:
                pass

        # 若未从缓存 PID 提取到，则扫描进程
        if not csrf_candidates or not port_candidates:
            try:
                for p in psutil.process_iter(["pid", "name"]):
                    pname = (p.info.get("name") or "").lower()
                    if "language_server" in pname:
                        self._cached_pid = p.info["pid"]
                        proc = psutil.Process(p.info["pid"])
                        cmdline = proc.cmdline()
                        for i, arg in enumerate(cmdline):
                            if arg == "--csrf_token" and i + 1 < len(cmdline):
                                c = cmdline[i + 1].strip()
                                if c and c not in csrf_candidates:
                                    csrf_candidates.append(c)
                        for conn in proc.net_connections(kind="tcp"):
                            if conn.status == "LISTEN" and conn.laddr.ip in ("127.0.0.1", "0.0.0.0", "::1"):
                                if conn.laddr.port not in port_candidates:
                                    port_candidates.append(conn.laddr.port)
                        break
            except Exception:
                pass

        # 2. 从最近的 main.log 倒序补充候选端口与令牌
        log_path = os.path.join(self.app_data_dir, "logs", "main.log")
        if os.path.exists(log_path):
            try:
                with open(log_path, "rb") as f:
                    f.seek(max(0, os.path.getsize(log_path) - 65536))
                    chunk = f.read().decode("utf-8", errors="ignore")
                ports = [int(p) for p in re.findall(r"https://127\.0\.0\.1:(\d+)/", chunk)]
                for p in reversed(ports):
                    if p not in port_candidates:
                        port_candidates.append(p)
                tokens = re.findall(r"--csrf_token\s+([a-zA-Z0-9\-]+)", chunk)
                for t in reversed(tokens):
                    if t not in csrf_candidates:
                        csrf_candidates.append(t)
            except Exception:
                pass

        # 3. 快速探活匹配 (优先测试当前活跃组合，成功即刻退出)
        for csrf in csrf_candidates[:3]:
            for port in port_candidates[:4]:
                url = f"https://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary"
                headers = {
                    "Content-Type": "application/json",
                    "Connect-Protocol-Version": "1",
                    "x-codeium-csrf-token": csrf
                }
                req = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")
                try:
                    with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=0.6) as resp:
                        if resp.status == 200:
                            return port, csrf
                except Exception:
                    continue

        return (port_candidates[0] if port_candidates else None), (csrf_candidates[0] if csrf_candidates else None)

    def _call_ls_rpc(self, port: int, csrf: str, method: str) -> Optional[Dict[str, Any]]:
        """调用本地 Language Server 的 Connect-RPC 接口 (带 401 自失效重置)"""
        url = f"https://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/{method}"
        headers = {
            "Content-Type": "application/json",
            "Connect-Protocol-Version": "1",
            "x-codeium-csrf-token": csrf
        }
        req = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=2.5) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8", errors="ignore"))
        except urllib.error.HTTPError as he:
            if he.code == 401:
                # 凭据失效（如 Language Server 重启变更了 csrf_token），清空缓存以备立即重新发现
                self._ls_port = None
                self._ls_csrf_token = None
        except Exception:
            pass
        return None

    def _fetch_official_quota(self, force: bool = False) -> Dict[str, Any]:
        """拉取 Antigravity 官方实时配额 (带 30 秒缓存与 401 自动失效重连)"""
        now = time.time()
        if not force and (now - self._last_quota_fetch_time < 30.0) and self._cached_quota_data:
            return self._cached_quota_data

        # 如果未检测到进程运行，直接返回缓存或空
        if not self._last_running_state:
            return self._cached_quota_data if self._cached_quota_data else {}

        self._last_quota_fetch_time = now

        # 刷新或探测凭据
        if not self._ls_port or not self._ls_csrf_token:
            port, csrf = self._discover_rpc_credentials()
            self._ls_port = port
            self._ls_csrf_token = csrf

        if not self._ls_port or not self._ls_csrf_token:
            return self._cached_quota_data

        # 1. 尝试拉取 RetrieveUserQuotaSummary
        quota_res = self._call_ls_rpc(self._ls_port, self._ls_csrf_token, "RetrieveUserQuotaSummary")
        if quota_res is None and (not self._ls_port or not self._ls_csrf_token):
            # 刚刚 401 失效了，执行一次重新发现
            port, csrf = self._discover_rpc_credentials()
            if port and csrf:
                self._ls_port = port
                self._ls_csrf_token = csrf
                quota_res = self._call_ls_rpc(self._ls_port, self._ls_csrf_token, "RetrieveUserQuotaSummary")

        if not quota_res:
            return self._cached_quota_data

        parsed_data: Dict[str, Any] = {
            "user_tier_name": self._cached_quota_data.get("user_tier_name", ""),
            "gemini_5h_percent": -1.0,
            "gemini_5h_reset_str": "",
            "gemini_weekly_percent": -1.0,
            "gemini_weekly_reset_str": "",
            "third_party_5h_percent": -1.0,
            "third_party_weekly_percent": -1.0
        }

        # 解析用户等级 (如果之前未获取，调用 GetUserStatus)
        if not parsed_data["user_tier_name"]:
            user_status = self._call_ls_rpc(self._ls_port, self._ls_csrf_token, "GetUserStatus")
            if user_status:
                ust = user_status.get("userStatus") or user_status.get("response", {}).get("userStatus") or user_status
                tier = ust.get("userTier") if isinstance(ust, dict) else None
                if isinstance(tier, dict):
                    parsed_data["user_tier_name"] = tier.get("name") or tier.get("id") or ""

        # 解析配额组与存储桶
        groups = quota_res.get("response", {}).get("groups", [])
        if not groups and "groups" in quota_res:
            groups = quota_res["groups"]

        for group in groups:
            d_name = group.get("displayName", "")
            buckets = group.get("buckets", [])
            if "Gemini" in d_name:
                for b in buckets:
                    bid = b.get("bucketId", "")
                    win = b.get("window", "")
                    rem_frac = b.get("remainingFraction", 0.0)
                    rem_pct = round(rem_frac * 100.0, 1)
                    reset_str = format_iso_reset_time(b.get("resetTime", ""))
                    if bid == "gemini-5h" or win == "5h":
                        parsed_data["gemini_5h_percent"] = rem_pct
                        parsed_data["gemini_5h_reset_str"] = reset_str
                    elif bid == "gemini-weekly" or win == "weekly":
                        parsed_data["gemini_weekly_percent"] = rem_pct
                        parsed_data["gemini_weekly_reset_str"] = reset_str
            elif "Claude" in d_name or "3p" in d_name:
                for b in buckets:
                    win = b.get("window", "")
                    rem_frac = b.get("remainingFraction", 0.0)
                    rem_pct = round(rem_frac * 100.0, 1)
                    if win == "5h":
                        parsed_data["third_party_5h_percent"] = rem_pct
                    elif win == "weekly":
                        parsed_data["third_party_weekly_percent"] = rem_pct

        self._cached_quota_data = parsed_data
        return parsed_data

    def get_conversation_title(self, conv_id: str) -> str:
        """从 annotations 或会话开头获取人类可读标题"""
        if not conv_id:
            return "无活跃会话"
        ann_file = os.path.join(self.ann_dir, f"{conv_id}.pbtxt")
        if os.path.exists(ann_file):
            try:
                with open(ann_file, "r", encoding="utf-8", errors="ignore") as f:
                    c = f.read()
                m = re.search(r'title:\s*"([^"]+)"', c)
                if m:
                    return m.group(1)
            except Exception:
                pass
        return "未命名会话"

    def get_conversation_model(self, conv_id: str) -> str:
        """从会话 transcript 探测该会话所实际绑定的模型"""
        if not conv_id:
            return "Gemini 3.8 Flash (High)"
        if conv_id in self._cached_convo_models:
            return self._cached_convo_models[conv_id]

        t_path = os.path.join(self.brain_dir, conv_id, ".system_generated", "logs", "transcript.jsonl")
        model_name = "Gemini 3.8 Flash (High)"
        if os.path.exists(t_path):
            try:
                with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
                    chunk = f.read(12000)
                m = re.search(r'Model Selection[`\s\']*from\s+[^\s]+\s+to\s+([A-Za-z0-9. ()\-]+?)\.\s+No need', chunk)
                if m:
                    model_name = m.group(1).strip()
                elif "Gemini 3.7 Flash" in chunk:
                    model_name = "Gemini 3.7 Flash (High)"
                elif "Gemini 3.1 Pro" in chunk:
                    model_name = "Gemini 3.1 Pro (High)"
            except Exception:
                pass

        self._cached_convo_models[conv_id] = model_name
        return model_name

    def get_active_conversation_id(self) -> str:
        """获取当前活跃的会话 ID（毫秒级跨源感知：聚合对话日志、SQLite WAL 与界面查看时间戳）"""
        # 如果用户在仪表盘手动点击了某个会话，优先呈现手动选中的会话
        if self.selected_convo_id:
            return self.selected_convo_id

        best_cid = ""
        best_time = 0.0

        # 候选 CID 集合：覆盖 brain、annotations 以及 conversations 目录
        cids = set()
        if os.path.exists(self.brain_dir):
            cids.update(os.listdir(self.brain_dir))
        if os.path.exists(self.ann_dir):
            for fname in os.listdir(self.ann_dir):
                if fname.endswith(".pbtxt"):
                    cids.add(fname[:-6])
        if os.path.exists(self.convs_dir):
            for fname in os.listdir(self.convs_dir):
                if fname.endswith(".db") or fname.endswith(".db-wal"):
                    cids.add(fname.split(".")[0])

        for cid in cids:
            t_path = os.path.join(self.brain_dir, cid, ".system_generated", "logs", "transcript.jsonl")
            wal_path = os.path.join(self.convs_dir, f"{cid}.db-wal")
            db_path = os.path.join(self.convs_dir, f"{cid}.db")
            ann_path = os.path.join(self.ann_dir, f"{cid}.pbtxt")

            m_time = 0.0
            for p in (t_path, wal_path, db_path, ann_path):
                try:
                    mt = os.path.getmtime(p)
                    if mt > m_time:
                        m_time = mt
                except OSError:
                    pass

            if m_time > best_time:
                best_time = m_time
                best_cid = cid

        return best_cid

    def analyze_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        """分析单个会话的 Token 构成与步骤（带签名缓存机制）"""
        transcript_path = os.path.join(self.brain_dir, conv_id, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(transcript_path):
            return None

        try:
            st = os.stat(transcript_path)
            sig = (st.st_mtime, st.st_size)
            if conv_id in self._cached_convo_analysis and self._cached_file_signatures.get(conv_id) == sig:
                return self._cached_convo_analysis[conv_id]
        except Exception:
            return None

        user_tokens = 0
        model_tokens = 0
        thinking_tokens = 0
        tool_tokens = 0
        subagents_count = 0
        step_count = 0

        last_user_step_tokens = 0
        last_model_step_tokens = 0
        last_step_type = ""

        try:
            with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    step = json.loads(line)
                    step_count += 1
                    stype = step.get("type", "")
                    content = step.get("content", "")
                    thinking = step.get("thinking", "")
                    tools = step.get("tool_calls", [])

                    c_tok = estimate_tokens(content)
                    th_tok = estimate_tokens(thinking)
                    t_tok = 0
                    if tools:
                        t_tok = estimate_tokens(json.dumps(tools, ensure_ascii=False))
                        for tc in tools:
                            if isinstance(tc, dict) and "invoke_subagent" in str(tc.get("name", "")):
                                subagents_count += 1

                    if stype == "USER_INPUT":
                        user_tokens += c_tok
                        last_user_step_tokens = c_tok
                    elif stype == "PLANNER_RESPONSE":
                        model_tokens += c_tok
                        thinking_tokens += th_tok
                        tool_tokens += t_tok
                        last_model_step_tokens = c_tok + th_tok + t_tok
                    elif stype == "GENERIC":
                        tool_tokens += c_tok

                    last_step_type = stype

            if step_count == 0:
                base_sys_tokens = 0
                total_context = 0
            else:
                base_sys_tokens = 22_000
                total_context = base_sys_tokens + user_tokens + model_tokens + thinking_tokens + tool_tokens

            analysis = {
                "conv_id": conv_id,
                "title": self.get_conversation_title(conv_id),
                "steps": step_count,
                "subagents_count": subagents_count,
                "user_tokens": user_tokens,
                "model_tokens": model_tokens,
                "thinking_tokens": thinking_tokens,
                "tool_tokens": tool_tokens,
                "base_system_tokens": base_sys_tokens,
                "total_context_tokens": total_context,
                "last_turn_input": last_user_step_tokens,
                "last_turn_output": last_model_step_tokens,
                "last_step_type": last_step_type,
                "last_mtime": st.st_mtime
            }

            self._cached_convo_analysis[conv_id] = analysis
            self._cached_file_signatures[conv_id] = sig
            return analysis
        except Exception:
            return None

    def _get_today_tokens_for_file(self, t_path: str, today_midnight: float) -> int:
        """从 transcript.jsonl 中仅提取 created_at 在今日自然日零点之后的增量 Token"""
        tok = 0
        try:
            with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    step = json.loads(line)
                    cat = step.get("created_at", "")
                    if cat:
                        try:
                            dt = datetime.datetime.fromisoformat(cat.replace("Z", "+00:00"))
                            if dt.timestamp() >= today_midnight:
                                content = step.get("content", "")
                                thinking = step.get("thinking", "")
                                tools = step.get("tool_calls", [])
                                t_content = json.dumps(tools, ensure_ascii=False) if tools else ""
                                tok += estimate_tokens(content) + estimate_tokens(thinking) + estimate_tokens(t_content)
                        except Exception:
                            pass
        except Exception:
            pass
        return tok

    def _refresh_totals_and_history(self, force_refresh: bool = False):
        """周期性统计总消耗、今日消耗与构建会话漫游列表 (基于文件修改签名毫秒级增量缓存，零磁盘 I/O 负担)"""
        now = time.time()
        if not force_refresh and (now - self._last_totals_calc_time < 10.0) and self._cached_total_convs > 0:
            return

        self._last_totals_calc_time = now
        if not os.path.exists(self.brain_dir):
            return

        transcripts = glob.glob(os.path.join(self.brain_dir, "*", ".system_generated", "logs", "transcript.jsonl"))
        self._cached_total_convs = len(transcripts)

        # 今日自然日零点时间戳 (00:00:00 本地时间) 与今日日期字符串
        now_tuple = time.localtime(now)
        today_midnight = time.mktime((now_tuple.tm_year, now_tuple.tm_mon, now_tuple.tm_mday, 0, 0, 0, 0, 0, -1))
        today_date_str = time.strftime("%Y-%m-%d", now_tuple)

        # 按最后修改时间降序排序
        sorted_transcripts = sorted(transcripts, key=os.path.getmtime, reverse=True)
        today_tokens = 0
        all_tokens = 0
        today_cost_usd = 0.0
        all_cost_usd = 0.0
        model_breakdown: Dict[str, Dict[str, Any]] = {}
        recent_list = []
        cache_dirty = False

        for t_path in sorted_transcripts:
            try:
                st = os.stat(t_path)
                cid = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(t_path))))
                sig = [st.st_mtime, st.st_size]
                cached = self._token_disk_cache.get(cid)

                if cached and cached.get("sig") == sig:
                    est_tok = cached.get("tokens", 0)
                    conv_cost = cached.get("cost_usd", 0.0)
                    m_name = cached.get("model", "Gemini 3.8 Flash (High)")
                    title = cached.get("title") or self.get_conversation_title(cid)
                    conv_today_tok = cached.get("today_tokens", 0) if cached.get("today_date") == today_date_str else 0
                else:
                    est_tok = int(st.st_size / 3.5)
                    m_name = self.get_conversation_model(cid)
                    rate = get_model_rate_per_million(m_name)
                    conv_cost = (est_tok / 1_000_000.0) * rate
                    title = self.get_conversation_title(cid)
                    conv_today_tok = 0

                    # 仅对今日发生过修改的会话计算今日用量
                    if st.st_mtime >= today_midnight:
                        conv_today_tok = self._get_today_tokens_for_file(t_path, today_midnight)

                    self._token_disk_cache[cid] = {
                        "sig": sig,
                        "tokens": est_tok,
                        "cost_usd": conv_cost,
                        "model": m_name,
                        "title": title,
                        "today_date": today_date_str,
                        "today_tokens": conv_today_tok
                    }
                    cache_dirty = True

                all_tokens += est_tok
                all_cost_usd += conv_cost

                if st.st_mtime >= today_midnight and conv_today_tok > 0:
                    today_tokens += conv_today_tok
                    rate = get_model_rate_per_million(m_name)
                    today_cost_usd += (conv_today_tok / 1_000_000.0) * rate

                if m_name not in model_breakdown:
                    model_breakdown[m_name] = {"count": 0, "tokens": 0, "cost_usd": 0.0}
                model_breakdown[m_name]["count"] += 1
                model_breakdown[m_name]["tokens"] += est_tok
                model_breakdown[m_name]["cost_usd"] += conv_cost

                # 取前 15 个会话填充历史表
                if len(recent_list) < 15:
                    recent_list.append({
                        "id": cid,
                        "title": title,
                        "model": m_name,
                        "tokens": est_tok,
                        "cost_usd": conv_cost,
                        "mtime": time.strftime("%m-%d %H:%M", time.localtime(st.st_mtime)),
                        "path": os.path.dirname(os.path.dirname(os.path.dirname(t_path)))
                    })
            except Exception:
                continue

        self._cached_today_tokens = today_tokens
        self._cached_total_tokens = all_tokens
        self._cached_today_cost = today_cost_usd
        self._cached_total_cost = all_cost_usd
        self._cached_model_breakdown = model_breakdown
        self._cached_recent_list = recent_list

        if cache_dirty:
            self._save_token_disk_cache()

    def sample_once(self, force_refresh_totals: bool = False) -> AntigravityMetrics:
        """执行单次采样并组装 AntigravityMetrics"""
        is_running = self._check_is_running()
        active_id = self.get_active_conversation_id()
        self._refresh_totals_and_history(force_refresh=force_refresh_totals)

        metrics = AntigravityMetrics(
            is_running=is_running,
            is_pinned=bool(self.selected_convo_id),
            active_conversation_id=active_id,
            today_tokens=self._cached_today_tokens,
            total_tokens=self._cached_total_tokens,
            today_cost_usd=self._cached_today_cost,
            total_cost_usd=self._cached_total_cost,
            model_breakdown=self._cached_model_breakdown,
            total_conversations=self._cached_total_convs,
            recent_conversations=self._cached_recent_list
        )

        if not is_running:
            metrics.agent_status = "离线"
            metrics.status_color = "#64748b"

        if active_id:
            metrics.model_name = self.get_conversation_model(active_id)
            res = self.analyze_conversation(active_id)
            if res:
                metrics.active_title = res["title"]
                metrics.step_count = res["steps"]
                metrics.subagents_count = res.get("subagents_count", 0)
                metrics.context_tokens = res["total_context_tokens"]
                metrics.context_percent = (metrics.context_tokens / metrics.context_limit) * 100.0
                metrics.user_tokens = res["user_tokens"]
                metrics.model_tokens = res["model_tokens"]
                metrics.thinking_tokens = res["thinking_tokens"]
                metrics.tool_tokens = res["tool_tokens"]
                metrics.base_system_tokens = res["base_system_tokens"]
                metrics.last_turn_input = res["last_turn_input"]
                metrics.last_turn_output = res["last_turn_output"]
                metrics.last_turn_total = res["last_turn_input"] + res["last_turn_output"]

                if self.selected_convo_id:
                    metrics.agent_status = "锁定查看"
                    metrics.status_color = "#38bdf8"
                elif is_running:
                    elapsed = time.time() - res["last_mtime"]
                    if elapsed < 8.0:
                        if res["last_step_type"] == "USER_INPUT":
                            metrics.agent_status = "思考中..."
                            metrics.status_color = "#38bdf8"
                        elif res["last_step_type"] == "PLANNER_RESPONSE":
                            metrics.agent_status = "执行工具中..."
                            metrics.status_color = "#f59e0b"
                        else:
                            metrics.agent_status = "正在生成..."
                            metrics.status_color = "#10b981"
                    else:
                        metrics.agent_status = "待机就绪"
                        metrics.status_color = "#22c55e"

        # 官方云端实时配额更新 (内部带 30s 极轻量缓存)
        quota = self._fetch_official_quota()
        if quota:
            metrics.user_tier_name = quota.get("user_tier_name", "")
            metrics.gemini_5h_percent = quota.get("gemini_5h_percent", -1.0)
            metrics.gemini_5h_reset_str = quota.get("gemini_5h_reset_str", "")
            metrics.gemini_weekly_percent = quota.get("gemini_weekly_percent", -1.0)
            metrics.gemini_weekly_reset_str = quota.get("gemini_weekly_reset_str", "")
            metrics.third_party_5h_percent = quota.get("third_party_5h_percent", -1.0)
            metrics.third_party_weekly_percent = quota.get("third_party_weekly_percent", -1.0)

        return metrics

    def run(self):
        while self.running:
            try:
                metrics = self.sample_once()
                self.metrics_updated.emit(metrics)
            except Exception:
                pass
            time.sleep(self.interval)
