package de.tormentor.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class ScreenLayoutTest {
    @Test public void phonesDoNotReserveTabletSidebarOrArtworkFrame() {
        for(int width:new int[]{320,360,393,412,480}) {
            assertTrue(ScreenLayout.compact(width));
            assertTrue(ScreenLayout.useFullSceneArea(width,600));
        }
        assertFalse(ScreenLayout.compact(800));
        assertTrue(ScreenLayout.useFullSceneArea(800,220));
        assertFalse(ScreenLayout.useFullSceneArea(800,600));
    }
    @Test public void narrowScreensAndLargeFontsUseOneColumn() {
        assertEquals(1,ScreenLayout.columns(320,1f));
        assertEquals(2,ScreenLayout.columns(393,1f));
        assertEquals(1,ScreenLayout.columns(393,1.5f));
    }
}
