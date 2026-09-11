"""Fixed-reference regional loss for numerical search, not visual acceptance.

Masks are frozen before search. Text regions are host-proposed evidence, not
OCR ground truth; the optimizer cannot move or shrink masks to improve loss.
"""

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat


class FixedRegionObjective:
    version = "fixed-regions-v1"

    def __init__(self, reference, bbox_norm, text_boxes_norm=()):
        with Image.open(reference) as source:
            source = source.convert("RGB")
        self.size = source.size
        self.box = self._box(bbox_norm)
        if self.box[2] <= self.box[0] or self.box[3] <= self.box[1]:
            raise ValueError("empty objective region")
        self.reference = source.crop(self.box)
        text = Image.new("L", self.size, 0)
        draw = ImageDraw.Draw(text)
        for bounds in text_boxes_norm:
            l, t, r, b = self._box(bounds)
            if r > l and b > t:
                draw.rectangle((l, t, r - 1, b - 1), fill=255)
        text = text.crop(self.box)
        edges = (
            self.reference.convert("L")
            .filter(ImageFilter.FIND_EDGES)
            .point(lambda p: 255 if p > 24 else 0)
        )
        # FIND_EDGES invents a frame at the image boundary.
        ImageDraw.Draw(edges).rectangle(
            (0, 0, edges.width - 1, edges.height - 1), outline=0
        )
        edges = edges.filter(ImageFilter.MaxFilter(3))
        contour = ImageChops.subtract(edges, text)
        background = ImageChops.invert(ImageChops.lighter(text, contour))
        self.masks = {"text": text, "contour": contour, "background": background}

    def _box(self, bounds):
        l, t, w, h = map(float, bounds)
        width, height = self.size
        return (
            max(0, min(width, round(l * width / 1000))),
            max(0, min(height, round(t * height / 1000))),
            max(0, min(width, round((l + w) * width / 1000))),
            max(0, min(height, round((t + h) * height / 1000))),
        )

    def evaluate(self, image):
        with Image.open(image) as actual:
            actual = actual.convert("RGB").resize(self.size).crop(self.box)
        difference = ImageChops.difference(actual, self.reference)
        losses = {}
        for name, mask in self.masks.items():
            if mask.getbbox() is not None:
                losses[name] = sum(ImageStat.Stat(difference, mask).mean) / (3 * 255)
        weights = {"text": 0.5, "contour": 0.35, "background": 0.15}
        total = sum(weights[name] for name in losses)
        return {
            "loss": sum(weights[name] * value for name, value in losses.items())
            / total,
            "regional_losses": losses,
            "reference_box_px": list(self.box),
            "mask_source": "fixed_reference_and_host_text_boxes",
            "version": self.version,
        }
