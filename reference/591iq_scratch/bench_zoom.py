"""把指定几张验证码放大单列，便于逐字确认真值（区分大小写 l/1、p、A/a）。"""
import os
import sys

from PIL import Image

BENCH = os.path.join(os.environ["TEMP"], "591iq_scratch", "ocrbench")


def main():
    for tag in sys.argv[1:]:
        src = os.path.join(BENCH, "r%s.jpg" % tag)
        im = Image.open(src).convert("L")
        im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
        out = os.path.join(BENCH, "zoom_%s.png" % tag)
        im.save(out)
        print(out, im.size)


if __name__ == "__main__":
    main()
