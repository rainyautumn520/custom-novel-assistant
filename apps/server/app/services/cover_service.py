import base64
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select

from app.config import settings
from app.core.database import new_id, project_db_path, project_session
from app.models.ai import CoverTask

COVER_PROMPT_TEMPLATE = (
    "你是资深小说封面插画师。绘制一张 2:3 竖版出版级封面插画，"
    "输出前逐条自检，必须符合以下全部要求：\n"
    "\n"
    "【构图】\n"
    "- 顶部 20% 为纯净书名区：只保留天空/虚化背景或暗部，禁止主体、"
    "关键元素或高对比细节侵入；\n"
    "- 底部 12% 为作者名区：保持暗部或留白，方便叠加文字；\n"
    "- 主体位于画面垂直中线偏下（黄金分割处），有明确视觉焦点与视线引导，"
    "前景-中景-背景层次分明；\n"
    "- 人物面部朝向留白侧，避免呆板正对画面；主体禁止贴边或出画。\n"
    "\n"
    "【光影与质感】\n"
    "- 电影级三点布光：强主光源 + 冷色环境光 + 轮廓光；"
    "体积光/丁达尔效应增强氛围；\n"
    "- 大气透视：前景清晰锐利，背景渐远渐虚；\n"
    "- 材质真实：皮肤、布料、金属、岩石、水、烟雾各有可信纹理，"
    "拒绝塑料感与橡皮质感。\n"
    "\n"
    "【色彩】\n"
    "- 全图统一主色调（暖金/冷青/暗红等，按题材而定），"
    "高对比、克制饱和、色调高级；\n"
    "- 禁止荧光色滥用、高饱和杂乱配色与廉价渐变。\n"
    "\n"
    "【内容与风格】\n"
    "- 场景内容：{prompt}；\n"
    "- 风格：{style}；\n"
    "- 画面必须完整可读、有叙事张力，禁止抽象色块、空白背景或未完成感。\n"
    "\n"
    "【硬性禁止】\n"
    "- 画面中绝对禁止出现任何文字、字母、数字、水印、logo、签名、网址；\n"
    "- 禁止低幼卡通、Q 版、廉价 3D 渲染、塑料玩具质感、贴纸拼贴感；\n"
    "- 禁止人物面部崩坏、五官错位、手指畸形、多指少指、肢体扭曲、透视错误；\n"
    "- 禁止过度留白、构图失衡、主体被裁切、模糊、噪点、压缩伪影。\n"
    "\n"
    "【输出】\n"
    "- 高分辨率、细节丰富、专业出版级完成度；只输出画面，不要任何文字说明。"
)

FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"

# 字体风格 -> 标题/作者名字体候选（按优先级；相对路径优先从 assets/fonts 查找）
FONT_STYLES = {
    "calligraphy": {
        "title": ["LXGWWenKai-Medium.ttf", "LXGWWenKai-Regular.ttf",
                  "C:/Windows/Fonts/simkai.ttf", "C:/Windows/Fonts/msyhbd.ttc"],
        "author": ["LXGWWenKai-Medium.ttf", "LXGWWenKai-Regular.ttf",
                   "C:/Windows/Fonts/simkai.ttf", "C:/Windows/Fonts/msyh.ttc"],
    },
    "serif": {
        "title": ["C:/Windows/Fonts/simsun.ttc", "C:/Windows/Fonts/simfang.ttf",
                  "C:/Windows/Fonts/msyhbd.ttc"],
        "author": ["C:/Windows/Fonts/simsun.ttc", "C:/Windows/Fonts/simfang.ttf",
                   "C:/Windows/Fonts/msyh.ttc"],
    },
    "sans": {
        "title": ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"],
        "author": ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"],
    },
    "round": {
        "title": ["C:/Windows/Fonts/simyou.ttf", "C:/Windows/Fonts/msyhbd.ttc"],
        "author": ["C:/Windows/Fonts/simyou.ttf", "C:/Windows/Fonts/msyh.ttc"],
    },
}

CALLIGRAPHY_KEYWORDS = [
    "玄幻", "仙侠", "古风", "武侠", "东方", "奇幻", "神话", "修真",
    "江湖", "剑", "龙", "仙", "神", "魔", "妖", "国风", "水墨",
]
SANS_KEYWORDS = ["科幻", "赛博", "都市", "悬疑", "刑侦", "未来", "机甲", "太空", "科技"]

# 主题配色：标题/作者名的渐变（顶→底）与描边色
STYLE_PALETTES = {
    "calligraphy": {
        "title": {"gradient": ((255, 233, 168), (176, 116, 22)), "stroke": (56, 30, 10)},
        "author": {"gradient": ((255, 255, 255), (232, 198, 130)), "stroke": (40, 22, 8)},
    },
    "serif": {
        "title": {"gradient": ((255, 248, 231), (212, 197, 159)), "stroke": (40, 28, 14)},
        "author": {"gradient": ((245, 238, 220), (196, 180, 142)), "stroke": (40, 28, 14)},
    },
    "sans": {
        "title": {"gradient": ((255, 255, 255), (188, 213, 255)), "stroke": (14, 32, 58)},
        "author": {"gradient": ((235, 242, 255), (168, 194, 236)), "stroke": (14, 32, 58)},
    },
    "round": {
        "title": {"gradient": ((255, 255, 255), (232, 205, 235)), "stroke": (58, 30, 60)},
        "author": {"gradient": ((255, 244, 250), (216, 176, 214)), "stroke": (58, 30, 60)},
    },
}


def resolve_font_style(font_style: str, prompt: str = "", style: str = "") -> str:
    """auto 时按题材关键词推断：古风→书法，科幻/都市→黑体，其余→宋体。"""
    if font_style and font_style != "auto":
        return font_style
    text = f"{prompt} {style}"
    if any(keyword in text for keyword in CALLIGRAPHY_KEYWORDS):
        return "calligraphy"
    if any(keyword in text for keyword in SANS_KEYWORDS):
        return "sans"
    return "serif"


def build_cover_prompt(raw_prompt: str, style: str = "") -> str:
    """把用户需求套入封面规范模板，保证生成结果符合封面构图。"""
    return COVER_PROMPT_TEMPLATE.format(
        style=style.strip() or "国风水墨与厚涂结合，写实与意境并重，东方奇幻史诗感",
        prompt=raw_prompt.strip() or "主角与标志性场景",
    )


def _load_font(size: int, style_key: str = "calligraphy", role: str = "title"):
    candidates = FONT_STYLES.get(style_key, FONT_STYLES["serif"])[role]
    for candidate in candidates:
        path = Path(candidate)
        if not path.is_absolute():
            path = FONT_DIR / candidate
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                continue
    return ImageFont.load_default()


def list_tasks(project_id: str) -> list[CoverTask]:
    with project_session(project_id) as session:
        return list(session.scalars(select(CoverTask).order_by(CoverTask.created_at.desc())))


def get_task_or_404(project_id: str, task_id: str) -> CoverTask:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        task = session.get(CoverTask, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        return task


def create_task(project_id: str, prompt: str, params: dict) -> CoverTask:
    """创建并同步执行封面生成任务（真实调用 Seedream 5.0）。"""
    task = CoverTask(
        id=new_id(),
        prompt=prompt,
        params=params,
        idempotency_key=new_id(),
        status="queued",
    )
    if not settings.seedream_api_key:
        task.status = "failed"
        task.error = "凭证未配置（AI_NOVEL_SEEDREAM_API_KEY），封面生成待联调启用"
        with project_session(project_id) as session:
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    final_prompt = build_cover_prompt(prompt, str(params.get("style", "")))
    _run_generation(project_id, task, final_prompt, params)
    with project_session(project_id) as session:
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def _run_generation(project_id: str, task: CoverTask, prompt: str, params: dict) -> None:
    """调用火山方舟 /images/generations，结果以 b64_json 或 url 保存到作品目录。"""
    try:
        resp = httpx.post(
            f"{settings.seedream_base_url.rstrip('/')}/images/generations",
            headers={"Authorization": f"Bearer {settings.seedream_api_key}"},
            json={
                "model": settings.seedream_model,
                "prompt": prompt,
                "size": params.get("size", "1920x2880"),
                "response_format": "b64_json",
            },
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()["data"][0]
        covers_dir = project_db_path(project_id).parent / "covers"
        covers_dir.mkdir(parents=True, exist_ok=True)
        target = covers_dir / f"{task.id}.png"
        if data.get("b64_json"):
            target.write_bytes(base64.b64decode(data["b64_json"]))
        elif data.get("url"):
            img = httpx.get(data["url"], timeout=90)
            img.raise_for_status()
            target.write_bytes(img.content)
        else:
            raise RuntimeError("响应中既无 b64_json 也无 url")
        task.status = "success"
        task.result_path = f"covers/{task.id}.png"
        task.optimized_prompt = prompt
    except httpx.HTTPStatusError as exc:
        task.status = "failed"
        try:
            detail = exc.response.json().get("error", {}).get("message") or exc.response.text
        except Exception:
            detail = exc.response.text[:300]
        task.error = f"生成失败（{exc.response.status_code}）：{detail}"
    except Exception as exc:  # 网络/超时/解析错误
        task.status = "failed"
        task.error = f"生成失败：{exc}"


def compose_cover(
    project_id: str,
    task_id: str,
    title: str,
    author: str,
    font_style: str = "auto",
    layout: str = "auto",
) -> CoverTask:
    """在生成图上叠加书名/作者名，输出新文件，不覆盖原图。"""
    from fastapi import HTTPException

    task = get_task_or_404(project_id, task_id)
    if not task.result_path:
        raise HTTPException(status_code=422, detail="该任务没有可合成的原图")
    root = project_db_path(project_id).parent
    source = root / task.result_path
    if not source.exists():
        raise HTTPException(status_code=404, detail="原图文件已丢失")

    image = Image.open(source).convert("RGBA")
    width, height = image.size

    # 顶部/底部渐变遮罩（替代生硬黑条）
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    mask_draw = ImageDraw.Draw(overlay)
    top_zone = int(height * 0.30)
    for y in range(top_zone):
        alpha = int(210 * (1 - y / top_zone))
        mask_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    bottom_zone = int(height * 0.24)
    for y in range(bottom_zone):
        alpha = int(245 * (y / bottom_zone))
        mask_draw.line(
            [(0, height - bottom_zone + y), (width, height - bottom_zone + y)],
            fill=(0, 0, 0, alpha),
        )
    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)
    resolved_style = resolve_font_style(font_style, title, "")
    palette = STYLE_PALETTES.get(resolved_style, STYLE_PALETTES["serif"])
    vertical = layout == "vertical"
    if layout == "auto" and resolved_style == "calligraphy":
        vertical = True  # 书法风格默认竖排（右侧）

    def render_artistic(
        text: str,
        font_size: int,
        role: str = "title",
        vertical: bool = False,
        y_anchor: float = 0.05,
        x_anchor: float = 0.78,
        spacing_ratio: float = 0.30,
        stroke_ratio: float = 0.030,
        backdrop: bool = False,
    ):
        min_size = max(10, int(width * 0.008))
        while True:
            font = _load_font(font_size, resolved_style, role)
            stroke = max(2, int(width * stroke_ratio))
            spacing = int(font_size * spacing_ratio)
            if vertical:
                total_h = font_size * len(text) + spacing * (len(text) - 1)
                fits = total_h <= height * 0.72 and (font_size + stroke * 2) <= width * 0.45
            else:
                char_widths = [
                    draw.textbbox((0, 0), ch, font=font, stroke_width=stroke)[2] for ch in text
                ]
                total_w = sum(char_widths) + spacing * (len(text) - 1)
                fits = total_w <= width * 0.92
            if fits or font_size <= min_size:
                break
            font_size = max(min_size, int(font_size * 0.85))

        stroke = max(2, int(width * stroke_ratio))
        spacing = int(font_size * spacing_ratio)
        if vertical:
            total_h = font_size * len(text) + spacing * (len(text) - 1)
            x = int(width * x_anchor)
            y = int(height * 0.10)
            positions = [(x, y + i * (font_size + spacing)) for i in range(len(text))]
        else:
            char_widths = [
                draw.textbbox((0, 0), ch, font=font, stroke_width=stroke)[2] for ch in text
            ]
            total_w = sum(char_widths) + spacing * (len(text) - 1)
            x = (width - total_w) / 2
            y = int(height * y_anchor)
            positions = []
            cursor = x
            for ch, cw in zip(text, char_widths):
                positions.append((cursor, y))
                cursor += cw + spacing

        # 半透明深色底衬（作者名专用，保证任何画面上可读）
        if backdrop:
            xs = [pos[0] for pos in positions]
            if vertical:
                pad_x, pad_y = font_size // 3, font_size // 4
                ys_back = [pos[1] for pos in positions]
                box = (
                    min(xs) - pad_x,
                    min(ys_back) - pad_y,
                    max(xs) + font_size + pad_x,
                    max(ys_back) + font_size + pad_y,
                )
            else:
                pad_x, pad_y = int(width * 0.02), int(font_size * 0.35)
                ys_back = [pos[1] for pos in positions]
                box = (
                    min(xs) - pad_x,
                    min(ys_back) - pad_y,
                    max(xs) + int(width * 0.01) + pad_x,
                    max(ys_back) + font_size + pad_y,
                )
            backdrop_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            ImageDraw.Draw(backdrop_layer).rounded_rectangle(
                box, radius=font_size // 2, fill=(10, 12, 18, 150)
            )
            image.alpha_composite(backdrop_layer)

        # 立体投影（深色偏移）
        for (px, py), ch in zip(positions, text):
            draw.text(
                (px + stroke, py + stroke),
                ch,
                font=font,
                fill=(0, 0, 0, 210),
                stroke_width=stroke,
                stroke_fill=(0, 0, 0, 210),
            )

        # 渐变描金文字图层
        layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        gradient, stroke_fill = palette[role]["gradient"], palette[role]["stroke"]
        for (px, py), ch in zip(positions, text):
            ld.text(
                (px, py),
                ch,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=stroke,
                stroke_fill=stroke_fill + (255,),
            )
        alpha = layer.split()[3]

        # 垂直渐变（按文字区域）
        ys = [int(pos[1]) for pos in positions]
        y0, y1 = min(ys), max(ys) + int(font_size)
        grad = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        for yy in range(max(0, y0), min(y1, height)):
            t = (yy - y0) / max(1, y1 - y0)
            col = tuple(int(gradient[0][i] + (gradient[1][i] - gradient[0][i]) * t) for i in range(3))
            gd.line([(0, yy), (width, yy)], fill=(*col, 255))
        colored = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        colored.paste(grad, (0, 0), alpha)

        # 顶部高光（叠白提亮）
        hi = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hi)
        hi_y1 = min(y1, y0 + int(font_size * 0.35))
        for yy in range(max(0, y0), max(y0, hi_y1)):
            t = 1 - (yy - y0) / max(1, hi_y1 - y0)
            hd.line([(0, yy), (width, yy)], fill=(255, 255, 255, int(110 * t)))
        colored = Image.alpha_composite(colored, hi)

        final = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        final.paste(colored, (0, 0), alpha)
        image.alpha_composite(final)

    if title.strip():
        render_artistic(
            title.strip(),
            max(48, int(width * 0.12)),
            role="title",
            vertical=vertical,
            y_anchor=0.05,
            x_anchor=0.78,
        )
    if author.strip():
        render_artistic(
            author.strip(),
            max(48, int(width * 0.065)),
            role="author",
            vertical=False,
            y_anchor=0.90,
            spacing_ratio=0.50,
            stroke_ratio=0.035,
            backdrop=True,
        )

    composed_path = f"covers/{task.id}_composed.png"
    (root / composed_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(root / composed_path)
    with project_session(project_id) as session:
        current = session.get(CoverTask, task_id)
        if current:
            current.composed_path = composed_path
            session.commit()
            session.refresh(current)
            return current
    task.composed_path = composed_path
    return task
