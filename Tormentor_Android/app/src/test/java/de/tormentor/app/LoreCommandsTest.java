package de.tormentor.app;
import org.junit.Test;
import static org.junit.Assert.*;

public class LoreCommandsTest {
    @Test public void recordingCommandsWorkAfterWakeAndDirectClick(){
        assertEquals(1,LoreCommands.action("Starte Aufnahme"));
        assertEquals(-1,LoreCommands.action("Beende die Aufnahme"));
        WakeGate gate=new WakeGate();
        assertEquals(1,LoreCommands.action(gate.accept("katana starte aufnahme",100)));
        assertNull(gate.accept("katana",200));
        assertEquals(-1,LoreCommands.action(gate.accept("beende aufnahme",300)));
    }
    @Test public void conversationAndMusicStopDoNotStopRecording(){
        assertEquals(0,LoreCommands.action("stoppe musik"));
        assertEquals(0,LoreCommands.action("stopp"));
        assertEquals(0,LoreCommands.action("starte aufnahme nicht"));
        assertNull(new WakeGate().accept("beende aufnahme",100));
    }
}
