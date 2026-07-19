package in.noticedesk.ocr.core;

import java.awt.Rectangle;

/**
 * Axis-aligned bounding box in pixel coordinates of the rasterized page,
 * origin at the top-left.
 */
public record BoundingBox(int x, int y, int width, int height) {

    public static BoundingBox from(Rectangle r) {
        return new BoundingBox(r.x, r.y, r.width, r.height);
    }
}
