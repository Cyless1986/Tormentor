package de.tormentor.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class WakeGateTest {
    @Test public void ignoresConversation(){WakeGate g=new WakeGate();assertNull(g.accept("spiele taverne",100));assertNull(g.accept("wir sagen stopp",200));assertNull(g.accept("cortanamusik",300));}
    @Test public void sameSentence(){WakeGate g=new WakeGate();assertEquals("spiele taverne",g.accept("hallo cortana spiele taverne",100));assertNull(g.accept("stopp",200));}
    @Test public void twoStageAndTimeout(){WakeGate g=new WakeGate();assertNull(g.accept("cortana",100));assertTrue(g.activated);assertEquals("spiele wald",g.accept("spiele wald",5000));assertNull(g.accept("stopp",5100));g.accept("cortana",6000);assertNull(g.accept("stopp",16001));}
    @Test public void stopClearsPendingWake(){WakeGate g=new WakeGate();g.accept("cortana",10);g.reset();assertNull(g.accept("stopp",20));}
    @Test public void acceptsKnownTranscriptions(){for(String word:new String[]{"cotana","contana","kortana","katana"})assertEquals("stopp",new WakeGate().accept(word+" stopp",100));}
}
