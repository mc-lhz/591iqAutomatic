"""把 24 张验证码拼成两张联系表（contact sheet），供读图能力一次性标定真值。"""
import os

from PIL import Image, ImageDraw

BENCH = os.path.join(os.environ["TEMP"], "591iq_scratch", "ocrbenchB")
PER = 8
COLS = 2
TW, TH = 520, 130


def cell(idx, src):
    im = Image.open(src).convert("L")
    w, h = im.width, im.height
    scale = min(TW / w, TH / h)
    im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    cellim = Image.new("L", (TW, TH), 255)
    cellim.paste(im, ((TW - im.width) // 2, (TH - im.height) // 2))
    out = Image.new("RGB", (TW, TH), (255, 255, 255))
    out.paste(cellim.convert("RGB"))
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, TW - 1, TH - 1], outline=(200, 200, 200))
    d.text((6, 4), "#%02d" % idx, fill=(200, 0, 0))
    return out


def main():
    files = sorted(f for f in os.listdir(BENCH) if f.endswith(".jpg"))
    for page in range(0, len(files), PER):
        chunk = files[page:page + PER]
        rows = (len(chunk) + COLS - 1) // COLS
        sheet = Image.new("RGB", (TW * COLS, TH * rows), (255, 255, 255))
        for k, f in enumerate(chunk):
            idx = page + k + 1
            sheet.paste(cell(idx, os.path.join(BENCH, f)),
                        ((k % COLS) * TW, (k // COLS) * TH))
        out = os.path.join(BENCH, "sheet_%02d.png" % (page // PER + 1))
        sheet.save(out)
        print(out, sheet.size, "含 #%02d-#%02d" % (page + 1, page + len(chunk)))


if __name__ == "__main__":
    main()

