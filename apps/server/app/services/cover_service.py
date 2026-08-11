import base64
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select

from app.config import settings
from app.core.database import new_id, project_db_path, project_session
from app.models.ai import CoverTask

COVER_PROMPT_TEMPLATE = (
    "为小说封面生成一张 2:3 竖版高品质插画，必须遵守以下硬性要求：\n"
    "1. 构图：主体场景居中偏下，顶部留出约 20% 高度作为书名区域，"
    "底部留出约 12% 高度作为作者名区域，人物/主体不要顶到画面上边缘；\n"
    "2. 内容：必须呈现一个完整清晰的叙事场景（人物/风景/建筑均可），"
    "有明确的视觉焦点与层次纵深，禁止抽象色块、纯装饰或不知所云的画面；\n"
    "3. 画面中禁止出现任何文字、字母、数字、水印、logo 或签名；\n"
    "4. 美术水准：对标专业出版级小说封面——强主光源与明确视觉焦点，"
    "丰富的材质细节，电影级景深与氛围，色彩高级协调、饱和但不刺眼；\n"
    "5. 风格：{style}；\n"
    "6. 画面内容需求：{prompt}；\n"
    "7. 禁忌：避免低幼卡通、廉价 3D 渲染、塑料质感、贴纸感、"
    "过度留白、构图失衡、脸部崩坏或比例失调。"
)

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def build_cover_prompt(raw_prompt: str, style: str = "") -> str:
    """把用户需求套入封面规范模板，保证生成结果符合封面构图。"""
    return COVER_PROMPT_TEMPLATE.format(
        style=style.strip() or "国风水墨与厚涂结合，写实与意境并重",
        prompt=raw_prompt.strip() or "主角与标志性场景",
    )


def _load_font(size: int):
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size)
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
    bottom_zone = int(height * 0.18)
    for y in range(bottom_zone):
        alpha = int(210 * (y / bottom_zone))
        mask_draw.line(
            [(0, height - bottom_zone + y), (width, height - bottom_zone + y)],
            fill=(0, 0, 0, alpha),
        )
    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)

    def draw_spaced_centered(
        text: str,
        font_size: int,
        y_ratio: float,
        spacing_ratio: float = 0.30,
        stroke_ratio: float = 0.030,
    ):
        min_size = max(10, int(width * 0.008))
        while True:
            font = _load_font(font_size)
            stroke = max(2, int(width * stroke_ratio))
            spacing = int(font_size * spacing_ratio)
            char_widths = [
                draw.textbbox((0, 0), ch, font=font, stroke_width=stroke)[2] for ch in text
            ]
            total_w = sum(char_widths) + spacing * (len(text) - 1)
            if total_w <= width * 0.92 or font_size <= min_size:
                break
            font_size = max(min_size, int(font_size * 0.85))
        x = (width - total_w) / 2
        y = int(height * y_ratio)
        for ch, cw in zip(text, char_widths):
            draw.text(
                (x + stroke, y + stroke),
                ch,
                font=font,
                fill=(0, 0, 0, 220),
                stroke_width=stroke,
                stroke_fill=(0, 0, 0, 220),
            )
            draw.text(
                (x, y),
                ch,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=stroke,
                stroke_fill=(18, 18, 28, 255),
            )
            x += cw + spacing

    if title.strip():
        draw_spaced_centered(title.strip(), max(48, int(width * 0.12)), 0.05)
    if author.strip():
        draw_spaced_centered(
            author.strip(),
            max(40, int(width * 0.055)),
            0.90,
            spacing_ratio=0.50,
            stroke_ratio=0.025,
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
