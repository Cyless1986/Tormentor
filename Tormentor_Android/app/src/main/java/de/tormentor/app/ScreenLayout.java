package de.tormentor.app;

/** Density-independent layout choices shared by phone and tablet views. */
final class ScreenLayout {
    static boolean compact(int widthDp) { return widthDp < 600; }
    static boolean useFullSceneArea(int widthDp, int heightDp) {
        return widthDp < 600 || heightDp < 480;
    }
    static int columns(int widthDp, float fontScale) {
        return widthDp < 360 || fontScale >= 1.3f ? 1 : 2;
    }
}
