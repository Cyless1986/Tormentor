package de.tormentor.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class WakeGateTest {
    @Test public void ignoresConversation(){WakeGate g=new WakeGate();assertNull(g.accept("spiele taverne",100));assertNull(g.accept("wir sagen stopp",200));assertNull(g.accept("cortanamusik",300));}
    @Test public void sameSentence(){WakeGate g=new WakeGate();assertEquals("spiele taverne",g.accept("cortana spiele taverne",100));assertNull(g.accept("stopp",200));}
    @Test public void twoStageAndTimeout(){WakeGate g=new WakeGate();assertNull(g.accept("cortana",100));assertTrue(g.activated);assertEquals("spiele wald",g.accept("spiele wald",5000));assertNull(g.accept("stopp",5100));g.accept("cortana",6000);assertNull(g.accept("stopp",16001));}
    @Test public void stopClearsPendingWake(){WakeGate g=new WakeGate();g.accept("cortana",10);g.reset();assertNull(g.accept("stopp",20));}
    @Test public void acceptsKnownTranscriptions(){for(String word:new String[]{"cortana","kortana","katana"})assertEquals("stopp",new WakeGate().accept(word+" stopp",100));}
    @Test public void rejectsConversationMentions(){for(String text:new String[]{"ich habe cortana gesagt","mein katana ist scharf","cotana","contana"}){WakeGate g=new WakeGate();assertNull(g.accept(text,100));assertFalse(g.activated);assertNull(g.accept("stopp",200));}}
    @Test public void tenSecondWindow(){WakeGate g=new WakeGate();g.accept("cortana",100);assertEquals("stopp",g.accept("stopp",10100));g.accept("cortana",20000);assertNull(g.accept("stopp",30001));}
    @Test public void friendlyWakePrefixes(){assertEquals("starte wald",new WakeGate().accept("Hey Cortana, starte wald",100));assertEquals("stopp",new WakeGate().accept("hallo katana stopp",100));assertNull(new WakeGate().accept("ich sage hey cortana stopp",100));}
    @Test public void identifiesWakeOnlyUtterances(){
        for(String text:new String[]{"cortana","hey katana","Hallo Cortana,"})assertTrue(WakeGate.isWakeOnly(text));
        for(String text:new String[]{"cortana stopp","hey katana spiele wald","ich sage cortana","stopp",""})assertFalse(WakeGate.isWakeOnly(text));
        WakeGate gate=new WakeGate();assertNull(gate.accept("cortana",100));assertTrue(gate.activated);
    }
}
