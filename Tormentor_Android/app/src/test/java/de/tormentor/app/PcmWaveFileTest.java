package de.tormentor.app;
import java.io.*;
import java.nio.*;
import java.nio.file.Files;
import org.junit.Test;
import static org.junit.Assert.*;

public class PcmWaveFileTest {
    @Test public void savedAudioHasValidHeaderWhileRecordingAndAfterClosing()throws Exception{
        File file=File.createTempFile("tormentor-lore-",".wav");
        try{
            PcmWaveFile recorder=new PcmWaveFile(file);
            recorder.write(new byte[]{1,2,3,4},4);
            ByteBuffer live=ByteBuffer.wrap(Files.readAllBytes(file.toPath())).order(ByteOrder.LITTLE_ENDIAN);
            assertEquals(4,live.getInt(40));assertEquals(16000,live.getInt(24));assertEquals(1,live.getShort(22));
            recorder.write(new byte[]{5,6},2);recorder.close();recorder.close();
            byte[] bytes=Files.readAllBytes(file.toPath());
            ByteBuffer saved=ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
            assertEquals(50,bytes.length);assertEquals(42,saved.getInt(4));assertEquals(6,saved.getInt(40));
            assertArrayEquals(new byte[]{1,2,3,4,5,6},java.util.Arrays.copyOfRange(bytes,44,50));
            try{recorder.write(new byte[]{7,8},2);fail("Closed recording must reject writes");}catch(IOException expected){}
        }finally{file.delete();}
    }
}
